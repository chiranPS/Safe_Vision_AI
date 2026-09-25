"""
KIE Stage — Key Information Extraction using PaddleOCR PP-Structure.
Identifies key-value pairs from form layouts.
"""
import logging
import os
from typing import List, Dict, Any, Optional

import cv2
import numpy as np

from ...models.pipeline_models import ExtractedField, KIEResult, OCRResult

logger = logging.getLogger(__name__)

# ── Singleton engine ──────────────────────────────────────────────────────────
_engine = None

def _get_engine():
    """Lazy-load KIE engine (DocUnderstanding or PPStructure)."""
    global _engine
    if _engine is None:
        try:
            # Disable PIR and oneDNN for stability on Windows
            os.environ['FLAGS_enable_pir_api'] = '0'
            os.environ['FLAGS_use_mkldnn'] = '0'
            
            # Try DocUnderstanding first (PaddleOCR v3 / PaddleX)
            try:
                from paddleocr import DocUnderstanding
                _engine = DocUnderstanding()
                logger.info("PaddleOCR DocUnderstanding (KIE) engine initialised.")
                return _engine
            except ImportError:
                pass
                
            # Fallback to PPStructure (PaddleOCR v2 style)
            from paddleocr import PPStructure
            _engine = PPStructure(kie=True, layout=True, show_log=False)
            logger.info("PP-Structure KIE engine initialised.")
        except Exception as exc:
            logger.warning(f"KIE engine unavailable: {exc}")
    return _engine


# ── Public entry-point ────────────────────────────────────────────────────────

async def extract(image_path: str, ocr_result: OCRResult) -> KIEResult:
    """
    Extract fields using a multi-stage approach:
    1. Try LLM (Gemini) for high-accuracy layout understanding.
    2. Try PP-Structure (Paddle) if LLM is unavailable.
    3. Fallback to Regex for reliability.
    """
    # ── Stage 1: LLM Extraction ──────────────────────────────────────────────
    from .llm_extractor import extract as llm_extract
    llm_res = llm_extract(ocr_result, image_path=image_path)
    if llm_res:
        logger.info("KIE: LLM extraction successful.")
        return llm_res

    # ── Stage 2: Model-based (Paddle) ────────────────────────────────────────
    engine = _get_engine()
    if not engine:
        # Fallback to regex-based field extractor
        from .field_extractor import extract as regex_extract
        return regex_extract(ocr_result)

    try:
        # PP-Structure requires a numpy image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
            
        # Run KIE analysis
        # In v3, predict returns a generator
        raw_result = engine.predict(img)
        
        # Convert generator to list if necessary
        if hasattr(raw_result, "__next__"):
             result = list(raw_result)
        else:
             result = raw_result
        
        extracted_data = _parse_kie_result(result, is_v3=hasattr(engine, "_paddlex_pipeline_name"))
        
        # Normalize and map to KIEResult
        mapped_result = _map_to_kie_result(extracted_data)
        
        # If PP-Structure didn't find much, merge with regex results
        if not mapped_result.complainant_name or not mapped_result.nic_number:
            from .field_extractor import extract as regex_extract
            reg_res = regex_extract(ocr_result)
            mapped_result = _merge_results(mapped_result, reg_res)
            
        return mapped_result

    except Exception as exc:
        logger.error(f"KIE PP-Structure failed: {exc}")
        # Final fallback
        from .field_extractor import extract as regex_extract
        return regex_extract(ocr_result)


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _parse_kie_result(result: List[Any], is_v3: bool = False) -> Dict[str, str]:
    """
    Parse KIE output. Handles both PP-Structure (v2) and DocUnderstanding (v3).
    """
    kv_pairs = {}
    
    if is_v3:
        # DocUnderstanding (v3) result format
        for res in result:
            # Each res has 'ocr_info'
            ocr_info = getattr(res, "ocr_info", []) if not isinstance(res, dict) else res.get("ocr_info", [])
            
            # Simple pairing logic: if we find a 'question' followed by an 'answer'
            # (Note: v3 often uses relationship mapping, but we'll use heuristic grouping)
            current_key = None
            for item in ocr_info:
                text = item.get("text", "")
                label = item.get("label", "").lower()
                
                if "question" in label or "key" in label:
                    current_key = text.lower().strip(": ")
                elif ("answer" in label or "value" in label) and current_key:
                    kv_pairs[current_key] = text.strip()
                    current_key = None
    else:
        # PP-Structure (v2) result format
        for region in result:
            if isinstance(region, dict) and region.get('type') == 'kie':
                res = region.get('res', [])
                current_key = None
                for item in res:
                    try:
                        text = item[1][0]
                        label = item[2]
                        if 'key' in label.lower():
                            current_key = text.lower().strip(': ')
                        elif 'value' in label.lower() and current_key:
                            kv_pairs[current_key] = text.strip()
                            current_key = None
                    except (IndexError, TypeError):
                        continue
                        
    return kv_pairs

def _map_to_kie_result(data: Dict[str, str]) -> KIEResult:
    """Map raw KV pairs to normalized KIEResult fields."""
    
    # Normalization mapping (Common labels -> Canonical keys)
    mappings = {
        "reference_number": ["reference", "ref no", "complaint number"],
        "date": ["date", "today's date"],
        "time": ["time", "current time"],
        "police_station": ["station", "police station"],
        "complainant_name": ["name", "full name", "complainant", "नाम", "నరుడు"],
        "nic_number": ["nic", "id no", "identity", "nic number"],
        "dob": ["dob", "date of birth", "birth date"],
        "gender": ["gender", "sex"],
        "phone": ["phone", "mobile", "contact"],
        "address": ["address", "residence"],
        "occupation": ["occupation", "job", "profession"],
        "employer_address": ["employer", "work address"],
        "email": ["email", "e-mail"],
        "incident_date": ["incident date", "date of incident"],
        "incident_time": ["incident time", "time of incident"],
        "location": ["location", "place", "incident location", "area"],
        "persons_involved": ["persons involved", "people"],
        "suspected_individuals": ["suspected", "suspects"],
        "vehicle_details": ["vehicle", "car details", "bike details"],
        "description": ["description", "details", "statement", "narrative"],
        "evidence_notes": ["additional notes", "evidence notes"],
        "receiving_officer_name": ["receiving officer", "officer name"],
        "badge_number": ["badge", "badge number"],
        "rank": ["rank"],
        "branch": ["branch"],
        "assigned_station": ["assigned station"],
        "date_received": ["date received"],
        "manual_notes": ["manual notes", "officer notes"]
    }
    
    extracted = {k: None for k in mappings.keys()}
    fields_list = []
    
    for raw_key, value in data.items():
        found = False
        for canonical, aliases in mappings.items():
            if any(alias in raw_key for alias in aliases):
                extracted[canonical] = value
                fields_list.append(ExtractedField(
                    key=canonical,
                    value=value,
                    confidence=0.9, # PP-Structure usually higher confidence
                    source="pp-structure"
                ))
                found = True
                break
        
        if not found:
            # Keep unknown fields too
            fields_list.append(ExtractedField(
                key=raw_key,
                value=value,
                confidence=0.8,
                source="pp-structure-raw"
            ))

    return KIEResult(
        fields=fields_list,
        reference_number=extracted.get("reference_number"),
        date=extracted.get("date"),
        time=extracted.get("time"),
        police_station=extracted.get("police_station"),
        complainant_name=extracted.get("complainant_name"),
        nic_number=extracted.get("nic_number"),
        dob=extracted.get("dob"),
        gender=extracted.get("gender"),
        phone=extracted.get("phone"),
        address=extracted.get("address"),
        occupation=extracted.get("occupation"),
        employer_address=extracted.get("employer_address"),
        email=extracted.get("email"),
        incident_date=extracted.get("incident_date"),
        incident_time=extracted.get("incident_time"),
        location=extracted.get("location"),
        persons_involved=extracted.get("persons_involved"),
        suspected_individuals=extracted.get("suspected_individuals"),
        vehicle_details=extracted.get("vehicle_details"),
        description=extracted.get("description"),
        evidence_notes=extracted.get("evidence_notes"),
        receiving_officer_name=extracted.get("receiving_officer_name"),
        badge_number=extracted.get("badge_number"),
        rank=extracted.get("rank"),
        branch=extracted.get("branch"),
        assigned_station=extracted.get("assigned_station"),
        date_received=extracted.get("date_received"),
        manual_notes=extracted.get("manual_notes")
    )

def _merge_results(primary: KIEResult, fallback: KIEResult) -> KIEResult:
    """Merge KIE results, preferring primary (model) but filling gaps with fallback (regex)."""
    
    merged_fields = primary.fields.copy()
    
    # Helper to check if a field is already in the list
    def has_field(key): return any(f.key == key for f in merged_fields)
    
    # List of all string fields to merge
    text_fields = [
        "reference_number", "date", "time", "police_station",
        "complainant_name", "nic_number", "dob", "gender", "phone", "address", 
        "occupation", "employer_address", "email",
        "incident_date", "incident_time", "location", "persons_involved", 
        "suspected_individuals", "vehicle_details", "description", "evidence_notes",
        "receiving_officer_name", "badge_number", "rank", "branch", 
        "assigned_station", "date_received", "manual_notes"
    ]
    
    for field_name in text_fields:
        p_val = getattr(primary, field_name)
        f_val = getattr(fallback, field_name)
        
        if not p_val and f_val:
            setattr(primary, field_name, f_val)
            if not has_field(field_name):
                merged_fields.append(ExtractedField(
                    key=field_name,
                    value=f_val,
                    confidence=0.7,
                    source="regex-fallback"
                ))
    
    # Merge boolean flags (Evidence checkboxes)
    bool_fields = [
        "has_photos", "has_medical_report", "has_cctv", 
        "has_witness_statement", "has_audio_recording", "has_other_evidence",
        "signature_present"
    ]
    for field_name in bool_fields:
        if not getattr(primary, field_name) and getattr(fallback, field_name):
            setattr(primary, field_name, True)
    
    primary.fields = merged_fields
    return primary
