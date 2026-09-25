import os
import json
import logging
import google.generativeai as genai
from typing import Optional
from ...models.pipeline_models import KIEResult, ExtractedField, OCRResult

logger = logging.getLogger(__name__)

import PIL.Image

def extract(ocr_result: OCRResult, image_path: Optional[str] = None) -> Optional[KIEResult]:
    """
    KIE Stage — Key Information Extraction using Gemini Flash.
    Converts raw OCR text (or image directly) into structured form data.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Skipping LLM extraction.")
        return None
    logger.info(f"Using GEMINI_API_KEY: {api_key[:10]}...")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Extract structured information from the following Sri Lanka Police Complaint Intake Form.
        Return ONLY a JSON object matching the schema below. 
        If a field is not found, use null for strings and false for booleans.
        Be extremely accurate. Remove any noise or hallucinations.
        
        JSON SCHEMA:
        {{
            "reference_number": "string (format: SLP-YYYY-XXXXXX)",
            "date": "string (format: YYYY-MM-DD)",
            "time": "string (form time)",
            "police_station": "string",
            "complaint_category_text": "string (text written in Other/Category)",
            "complainant_name": "string",
            "nic_number": "string",
            "dob": "string (format: YYYY-MM-DD)",
            "gender": "string (Male/Female)",
            "phone": "string",
            "address": "string",
            "occupation": "string",
            "employer_address": "string",
            "email": "string",
            "incident_date": "string (format: YYYY-MM-DD)",
            "incident_time": "string",
            "location": "string",
            "persons_involved": "string",
            "suspected_individuals": "string",
            "vehicle_details": "string",
            "description": "string",
            "evidence_notes": "string",
            "receiving_officer_name": "string",
            "badge_number": "string",
            "rank": "string",
            "branch": "string",
            "assigned_station": "string",
            "date_received": "string (format: YYYY-MM-DD)",
            "manual_notes": "string",
            "has_photos": boolean,
            "has_medical_report": boolean,
            "has_cctv": boolean,
            "has_witness_statement": boolean,
            "has_audio_recording": boolean,
            "has_other_evidence": boolean,
            "is_theft": boolean,
            "is_assault": boolean,
            "is_narcotics": boolean,
            "is_traffic": boolean,
            "is_domestic_violence": boolean,
            "is_child_abuse": boolean,
            "is_suspicious_activity": boolean,
            "is_other_category": boolean
        }}
        """
        
        contents = [prompt]
        if image_path and os.path.exists(image_path):
            ext = image_path.lower().split('.')[-1]
            if ext in ['png', 'jpg', 'jpeg', 'webp', 'heic', 'heif']:
                img = PIL.Image.open(image_path)
                contents.append(img)
            elif ext == 'pdf':
                import fitz
                doc = fitz.open(image_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                img_data = pix.tobytes("png")
                import io
                img = PIL.Image.open(io.BytesIO(img_data))
                contents.append(img)
                doc.close()
            else:
                contents[0] += f"\n\nOCR TEXT:\n\"\"\"{ocr_result.raw_text}\"\"\""
        else:
            # Fallback to OCR text if image cannot be passed
            contents[0] += f"\n\nOCR TEXT:\n\"\"\"{ocr_result.raw_text}\"\"\""

        models_to_try = ['gemini-2.5-flash', 'gemini-3-flash-preview', 'gemini-1.5-flash-8b']
        response = None
        import time
        
        for attempt in range(2): # Try 2 times overall for rate limits
            for model_name in models_to_try:
                try:
                    logger.info(f"Attempting extraction with {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
                    break
                except Exception as e:
                    if '429' in str(e) or 'quota' in str(e).lower():
                        logger.warning(f"Quota exceeded/Rate limit for {model_name}: {e}")
                        continue
                    else:
                        raise e
            
            if response:
                break
            elif attempt == 0:
                logger.warning("All models failed due to rate limits. Waiting 10 seconds before retry...")
                time.sleep(10)
                
        if not response:
            logger.error("Failed to extract using Gemini after all retries and model fallbacks.")
            return None

        data = json.loads(response.text)
        
        # Convert JSON to KIEResult
        fields = []
        for k, v in data.items():
            if v and not isinstance(v, bool):
                fields.append(ExtractedField(key=k, value=str(v), confidence=0.95, source="llm-gemini"))

        return KIEResult(
            fields=fields,
            reference_number=data.get("reference_number"),
            date=data.get("date"),
            time=data.get("time"),
            police_station=data.get("police_station"),
            complaint_category=data.get("complaint_category_text"),
            complainant_name=data.get("complainant_name"),
            nic_number=data.get("nic_number"),
            dob=data.get("dob"),
            gender=data.get("gender"),
            phone=data.get("phone"),
            address=data.get("address"),
            occupation=data.get("occupation"),
            employer_address=data.get("employer_address"),
            email=data.get("email"),
            incident_date=data.get("incident_date"),
            incident_time=data.get("incident_time"),
            location=data.get("location"),
            persons_involved=data.get("persons_involved"),
            suspected_individuals=data.get("suspected_individuals"),
            vehicle_details=data.get("vehicle_details"),
            description=data.get("description"),
            evidence_notes=data.get("evidence_notes"),
            receiving_officer_name=data.get("receiving_officer_name"),
            badge_number=data.get("badge_number"),
            rank=data.get("rank"),
            branch=data.get("branch"),
            assigned_station=data.get("assigned_station"),
            date_received=data.get("date_received"),
            manual_notes=data.get("manual_notes"),
            has_photos=data.get("has_photos", False),
            has_medical_report=data.get("has_medical_report", False),
            has_cctv=data.get("has_cctv", False),
            has_witness_statement=data.get("has_witness_statement", False),
            has_audio_recording=data.get("has_audio_recording", False),
            has_other_evidence=data.get("has_other_evidence", False),
            is_theft=data.get("is_theft", False),
            is_assault=data.get("is_assault", False),
            is_narcotics=data.get("is_narcotics", False),
            is_traffic=data.get("is_traffic", False),
            is_domestic_violence=data.get("is_domestic_violence", False),
            is_child_abuse=data.get("is_child_abuse", False),
            is_suspicious_activity=data.get("is_suspicious_activity", False),
            is_other_category=data.get("is_other_category", False)
        )

    except Exception as exc:
        logger.error(f"Gemini KIE failed: {exc}")
        return None
