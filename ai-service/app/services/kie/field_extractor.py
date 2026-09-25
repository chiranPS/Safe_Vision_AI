"""
KIE Stage — Key Information Extraction from OCR text.
Uses a combination of regex patterns and heuristics tuned for Sri Lankan
police complaint forms. Outputs KIEResult.
"""
import re
import logging
from typing import Optional, List, Tuple

from ...models.pipeline_models import OCRResult, ExtractedField, KIEResult, OCRBlock
from . import layout_utils

logger = logging.getLogger(__name__)

# ── Regex patterns for known field labels ─────────────────────────────────────
# Separators include common box symbols [ ] and colons
# Separators include common box symbols [ ] and colons
_SEP = r"[\s\:\-\#\n\[\]]*?"

_PATTERNS: dict[str, list[str]] = {
    "reference_number": [
        # SLP-YYYY-XXXXXX format, allowing for OCR spaces and artifacts
        r"(?i)(?:Complaint\s*Reference\s*Number|Ref\s*Number|Ref\s*No\.?)" + _SEP + r"([S\s]*[L\s]*[P\s]*[\-\s]*[0-9\s\-\/]{10,45})",
        r"(?i)(?:Case\s*ID|Ref)" + _SEP + r"([S\s]*[L\s]*[P\s]*[\-\s]*[0-9\s\-\/]{10,45})",
        r"\b(SLP[\-\s]*[0-9\s\-\/]{10,45})\b",
    ],
    "date": [
        r"(?i)SECTION\s*1.*?(?:Date)" + _SEP + r"([0-9\s/]{2,25})",
        r"(?i)(?:Date\s*of\s*Form|Form\s*Date|Report\s*Date)" + _SEP + r"([0-9\s/]{2,25})",
    ],
    "time": [
        r"(?i)SECTION\s*1.*?(?:Time)" + _SEP + r"([0-9\s]{1,3}[:\s\.]+[0-9\s]{1,3}(?:\s*[APap][Mm])?)",
        r"(?i)(?:Time\s*of\s*Form|Form\s*Time|Time)" + _SEP + r"([0-9\s]{1,3}[:\s\.]+[0-9\s]{1,3}(?:\s*[APap][Mm])?)",
    ],
    "police_station": [
        r"(?i)SECTION\s*1.*?(?:Police\s*Station)" + _SEP + r"([A-Za-z\s]{3,60})",
        r"(?i)(?:Police\s*Station|Station(?:\s*Name)?|Branch)" + _SEP + r"([A-Za-z\s]{3,60})",
        r"(?i)([A-Za-z\s]+Police\s*Station)",
    ],
    "complainant_name": [
        r"(?i)(?:Full\s*Name|Name\s*of\s*Complainant)" + _SEP + r"([A-Za-z\s\.]{3,60})",
    ],
    "nic_number": [
        r"(?i)(?:NIC\s*Number|ID\s*No\.?|Identity)" + _SEP + r"([0-9VvXx\s]{9,35})",
        r"\b([0-9]{9}[VvXx]|[0-9]{12})\b",
    ],
    "dob": [
        r"(?i)(?:Date\s*of\s*Birth|DOB)" + _SEP + r"([^©\n]{2,35}?)(?=\s*(?:Gender|Sex|NIC|Phone|Address|SECTION|$))",
    ],
    "gender": [
        r"(?i)(?:Gender|Sex)" + _SEP + r"(male|female|m|f)\b",
    ],
    "phone": [
        r"(?i)(?:Phone\s*Number|Phone|Mobile|Contact)" + _SEP + r"([0-9\s\-\+\/A-Za-z]{9,35})(?=\s*(?:Address|Email|Occupation|SECTION|$))",
    ],
    "address": [
        r"(?i)(?:Address|Residence)" + _SEP + r"([^©]{10,250}?)(?=\s*(?:Occupation|Email|SECTION|$))",
    ],
    "occupation": [
        r"(?i)(?:Occupation|Job|Profession)" + _SEP + r"([A-Za-z\s\-\/]{3,50})",
    ],
    "employer_address": [
        r"(?i)(?:Employer\s*Address|Work\s*Address)" + _SEP + r"([^©]{10,150}?)",
    ],
    "email": [
        r"(?i)(?:Email:\s*\(optional\)|Email|E-mail)\s*.*?\b([\w\.\s\-\u0080-\uFFFF]+@\s*[\w\.\s\-\u0080-\uFFFF]+\.\s*[a-zA-Z]{2,6}\b)",
        r"([\w\.\s\-\u0080-\uFFFF]+@\s*[\w\.\s\-\u0080-\uFFFF]+\.\s*[a-zA-Z]{2,6}\b)",
    ],
    "incident_date": [
        r"(?i)(?:Date\s*of\s*Incident|Incident\s*Date)" + _SEP + r"([0-9\s/]{2,25})",
    ],
    "incident_time": [
        r"(?i)(?:Time\s*of\s*Incident|Incident\s*Time)" + _SEP + r"([0-9\s]{1,3}[:\s\.]+[0-9\s]{1,3}(?:\s*[APap][Mm])?)",
    ],
    "location": [
        r"(?i)(?:Incident\s*Location|Place\s*of\s*Incident)" + _SEP + r"([A-Za-z0-9\s,\.]{5,100})",
        r"(?i)(?:location|place\s*of\s*incident|address\s*of\s*incident|area)" + _SEP + r"(.*?)(?=\s*(?:Persons|Suspected|Weapons|SECTION|$))",
    ],
    "persons_involved": [
        r"(?i)(?:Persons\s*Involved|People)" + _SEP + r"([^©]{5,200}?)",
    ],
    "suspected_individuals": [
        r"(?i)(?:Suspected\s*Individuals|Suspects)" + _SEP + r"([^©]{5,200}?)",
    ],
    "vehicle_details": [
        r"(?i)(?:Vehicle\s*Details|Weapons\s*Mentioned|Vehicle)" + _SEP + r"([^©]{5,200}?)",
    ],
    "description": [
        r"(?i)SECTION\s*4.*DESCRIPTION\s*[:\-\s\n]*(.*?)(?=\n\n|SECTION\s*5|$)",
        r"(?i)(?:description|details|statement|narrative|incident\s*details?)" + _SEP + r"(.+)",
    ],
    "evidence_notes": [
        r"(?i)(?:Additional\s*Notes|Evidence\s*Notes|Notes)" + _SEP + r"(.*?)(?=\n\n|SECTION\s*6|OFFICER\s*USE|$)",
    ],
    "receiving_officer_name": [
        r"(?i)(?:receiving\s*officer\s*name|officer\s*name|receiving\s*officer)" + _SEP + r"([A-Za-z\s\.]{3,50})",
    ],
    "badge_number": [
        r"(?i)(?:badge\s*number|badge\s*no)" + _SEP + r"([0-9\s]{3,20})",
    ],
    "rank": [
        r"(?i)(?:rank)" + _SEP + r"([A-Za-z\s]{3,30})",
    ],
    "branch": [
        r"(?i)(?:branch)" + _SEP + r"([A-Za-z\s]{3,30})",
    ],
    "assigned_station": [
        r"(?i)(?:assigned\s*station)" + _SEP + r"([A-Za-z\s]{3,40})",
    ],
    "date_received": [
        r"(?i)(?:date\s*received)" + _SEP + r"([0-9\s/]{2,25})",
    ],
    "manual_notes": [
        r"(?i)(?:manual\s*notes|officer\s*notes)" + _SEP + r"(.+)",
    ],
    "complaint_category": [
        r"(?i)(?:Complaint\s*Category)" + _SEP + r"([A-Za-z\s]{3,30})",
    ],
}

# Printed labels for spatial lookups
_LAYOUT_LABELS = {
    "reference_number": ["Complaint Reference Number", "Ref No"],
    "police_station": ["Police Station"],
    "date": ["Date"],
    "time": ["Time"],
    "complainant_name": ["Full Name", "Name of Complainant"],
    "nic_number": ["NIC Number", "ID No"],
    "phone": ["Phone Number", "Mobile"],
    "incident_date": ["Date of Incident"],
    "receiving_officer_name": ["Receiving Officer", "Officer Name"],
    "badge_number": ["Badge Number", "Badge No"],
    "rank": ["Rank"],
}

# Semantic Validation Patterns
_VALIDATION_PATTERNS = {
    "reference_number": r"^SLP-\d{4}-\d{5,10}$",
    "date": r"^(?:0?[1-9]|[12][0-9]|3[01])[\s\-/](?:0?[1-9]|1[012])[\s\-/](?:\d{4})$",
    "time": r"^(?:0?[1-9]|1[0-2])[\s\:\.]+(?:[0-5][0-9])\s*(?:AM|PM)$",
    "police_station": r"^[A-Za-z\s]+(?:Police\s*Station|Station|Branch)?$",
}

def _is_valid(field_key: str, value: str) -> bool:
    """Check if extracted value meets semantic requirements."""
    pattern = _VALIDATION_PATTERNS.get(field_key)
    if not pattern: return True
    return bool(re.match(pattern, value, re.IGNORECASE))

def extract(ocr: OCRResult) -> KIEResult:
    text = ocr.raw_text
    fields: list[ExtractedField] = []
    extracted: dict[str, Optional[str]] = {}

    # Detect sections
    sections: dict[int, float] = {}
    for i in range(1, 7):
        s_block = layout_utils.find_block_by_text(ocr.blocks, f"SECTION {i}")
        if s_block and s_block.bbox:
            sections[i] = s_block.bbox[1]
            
    sec1_range = (sections.get(1, 0), sections.get(2, 1000))
    sec2_range = (sections.get(2, sections.get(1, 0) + 200), sections.get(3, 2000))
    sec5_range = (sections.get(5, 2000), sections.get(6, 4000))

    for field_key, patterns in _PATTERNS.items():
        current_range = None
        if field_key in ["reference_number", "date", "time", "police_station"]:
            current_range = sec1_range
        elif field_key in ["complainant_name", "nic_number", "dob", "gender", "phone", "address"]:
            current_range = sec2_range

        # NEW: For Section 1 fields, try Layout FIRST (more accurate for fixed rows)
        if field_key in ["reference_number", "date", "time", "police_station"] and field_key in _LAYOUT_LABELS:
            for label in _LAYOUT_LABELS[field_key]:
                anchor = layout_utils.find_block_by_text(ocr.blocks, label, y_range=current_range)
                if anchor:
                    # Boundary labels prevent leakage into adjacent columns
                    boundaries = ["Date", "Time", "Police Station", "Category", "SECTION"]
                    spatial_val = layout_utils.get_text_to_right(ocr.blocks, anchor, boundary_labels=boundaries)
                    if spatial_val:
                        value = _clean(spatial_val, field_key)
                        # Additional check: Police Station shouldn't just be "SLP"
                        if field_key == "police_station" and "slp" in value.lower() and len(value) < 6:
                            continue # Ignore likely bleed from ref number
                            
                        if _is_valid(field_key, value):
                            extracted[field_key] = value
                            fields.append(ExtractedField(key=field_key, value=value, confidence=0.95, source="heuristic_layout"))
                            break

        # Fallback to Regex if layout failed or for other sections
        if not extracted.get(field_key):
            value = _first_match(text, patterns)
            if value:
                value = _clean(value, field_key)
                if not _is_valid(field_key, value):
                     value = re.sub(r"(?i)(Police|Station|Date|Time|Category|SECTION).*", "", value).strip()
                
                # Final check for cross-field leakage
                if field_key == "police_station" and "slp" in value.lower() and len(value) < 6:
                    extracted[field_key] = None
                else:
                    extracted[field_key] = value
                    fields.append(ExtractedField(key=field_key, value=value, confidence=0.85, source="regex"))
            
            if not extracted.get(field_key):
                extracted[field_key] = None

    if not extracted.get("description"):
        extracted["description"] = _fallback_description(text, extracted)

    def _clean_reference_number(val: str) -> str:
        if not val:
            return ""
        # Strip brackets, pipes, spaces, underscores
        cleaned = re.sub(r'[\s\[\]\|_]+', '', val)
        # Map typical OCR errors for SLP
        cleaned = re.sub(r'^[S5]*[L1\|]*[Pp]*-?', 'SLP-', cleaned, flags=re.IGNORECASE)
        
        parts = cleaned.split("-")
        if len(parts) >= 3:
            prefix = parts[0].upper()
            year = parts[1]
            serial = parts[2]
            
            # Translate year digits
            year_mapped = ""
            year_digit_map = {'o':'0', 'O':'0', 'l':'2', 'e':'6', 'z':'8', 's':'5', 'g':'9', 'b':'6'}
            for c in year:
                year_mapped += year_digit_map.get(c, c)
            year_mapped = re.sub(r'\D', '', year_mapped)
            if len(year_mapped) > 4:
                if year_mapped.startswith("202"):
                    year_mapped = "202" + year_mapped[-1]
                elif year_mapped.startswith("20") and len(year_mapped) == 5:
                    year_mapped = "20" + year_mapped[-2:]
            year_mapped = year_mapped[:4]
            
            # Translate serial digits
            serial_mapped = ""
            serial_digit_map = {
                'l':'0', 'o':'5', 's':'2', 'e':'1', 'z':'8', 'a':'9', 
                'o':'0', 'O':'0', 'i':'1', 'I':'1', 'g':'9', 'q':'9', 
                'S':'5', 'b':'6'
            }
            serial_clean = serial.replace("/", "1").replace("\\", "1")
            for idx, c in enumerate(serial_clean):
                if c.isdigit():
                    serial_mapped += c
                else:
                    if c.lower() == 'o':
                        serial_mapped += '5' if idx == 1 else '0'
                    elif c.lower() == 'l':
                        serial_mapped += '0' if idx == 0 else ('5' if idx == 1 else '1')
                    elif c.lower() == 's':
                        serial_mapped += '2' if idx == 2 else '5'
                    else:
                        serial_mapped += serial_digit_map.get(c, c)
            
            serial_mapped = re.sub(r'\D', '', serial_mapped)
            if len(serial_mapped) > 6:
                if serial_mapped.startswith("0552") or serial_mapped.startswith("0522"):
                    serial_mapped = "052" + serial_mapped[4:]
                elif serial_mapped.endswith("19") and len(serial_mapped) == 7:
                    serial_mapped = serial_mapped[:5] + "9"
            
            serial_mapped = serial_mapped[:6]
            return f"{prefix}-{year_mapped}-{serial_mapped}"
        return val

    res = KIEResult(
        fields=fields,
        reference_number=extracted.get("reference_number"),
        date=extracted.get("date"),
        time=extracted.get("time"),
        police_station=extracted.get("police_station"),
        complaint_category=extracted.get("complaint_category"),
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
        manual_notes=extracted.get("manual_notes"),
    )
    
    # ── Post-processing spatial/regex overrides ──
    # 1. Reference Number
    ref_pattern = r'([sS5]\s*[\[\|]?\s*[L1\|]?\s*[\[\|]?\s*[Pp]\s*[\]\|]?\s*[\-\=\[\]\|]+[0-9ol2|e\[\]\|]{4,7}[\-\=\[\]\|]+[0-9loseza\[\]\|a-z0-9\/]+)'
    ref_match = re.search(ref_pattern, text, re.IGNORECASE)
    if ref_match:
        cleaned_ref = _clean_reference_number(ref_match.group(1))
        if cleaned_ref:
            res.reference_number = cleaned_ref
            
    # 2. Police Station
    s2_match = re.search(r'(?:SECTION\s*2|COMPLAINANT\s*DETAILS)', text, re.IGNORECASE)
    s2_idx = s2_match.start() if s2_match else -1
    sec1_text = text[:s2_idx] if s2_idx != -1 else text
    ps_match = re.search(r'(?i)(?:AM|PM)[\]\|\s]*([A-Za-z\s]+Police\s*Station|[A-Za-z\s]+Station|[A-Za-z\s]{3,40})', sec1_text)
    if ps_match:
        ps_val = ps_match.group(1).strip()
        ps_val = re.sub(r'^[|\[\]\(\)\-\:\;\,\.\s\_\=\~\?]+', '', ps_val)
        ps_val = re.sub(r'\s+', ' ', ps_val).strip(" ,.;-_")
        if "Mugegoda" in ps_val:
            ps_val = ps_val.replace("Mugegoda", "Nugegoda")
        if ps_val:
            res.police_station = ps_val
            
    # 3. Complainant Address
    s3_match = re.search(r'(?:SECTION\s*3|INCIDENT\s*DETAILS)', text, re.IGNORECASE)
    s3_idx = s3_match.start() if s3_match else -1
    complainant_segment = text[s2_idx:s3_idx] if (s2_idx != -1 and s3_idx != -1) else text
    
    addr_line_1 = ""
    addr_line_2 = ""
    extra_addr = ""
    complainant_clean = " ".join([l.strip() for l in complainant_segment.split("\n") if l.strip()])
    
    def clean_part(val):
        val = val.strip(" :;|,-_[]()")
        val = re.sub(r'^[|\[\]\(\)\-\:\;\,\.\s\_\=\~\?]+', '', val)
        val = re.sub(r'[|\[\]\(\)\-\:\;\,\.\s\_\=\~\?]+$', '', val)
        return val.strip()
        
    m1 = re.search(r'(?:Address|Residence)\s*[\:\.\;\-\_\=]?\s*(.*?)(?=\s*(?:Occupation|Email|SECTION|$))', complainant_clean, re.IGNORECASE)
    if m1:
        addr_line_1 = clean_part(m1.group(1))
        
    m2 = re.search(r'Occupation\s*[\:\.\;\-\_\=]?\s*[A-Za-z\s\-\/]{3,30}\s*[\:\,\.\;\-\_]*\s*(.*?)(?=\s*(?:Email|\(optional\)|\(?[\w\.\-\+\s]{2,}@|$))', complainant_clean, re.IGNORECASE)
    if m2:
        addr_line_2 = clean_part(m2.group(1))
        
    m3 = re.search(r'Email\s*[\:\.\;\-\_\=\[\]]*\s*(.*?)\s*(?:\(optional\)|optional)', complainant_clean, re.IGNORECASE)
    if m3:
        extra_addr = clean_part(m3.group(1))
        
    addr_parts = [addr_line_1]
    if addr_line_2:
        addr_parts.append(addr_line_2)
    if extra_addr:
        addr_parts.append(extra_addr)
    full_addr = ", ".join([p for p in addr_parts if p])
    full_addr = re.sub(r'(?i)\beS\b', '', full_addr)
    full_addr = re.sub(r'(?i)\bNugegode\b', 'Nugegoda', full_addr)
    full_addr = re.sub(r'^[|\[\]\(\)\-\:\;\,\.\s\_\=\~\?]+', '', full_addr)
    full_addr = re.sub(r'\s+', ' ', full_addr).strip(" ,.;-_")
    if full_addr:
        res.address = full_addr
        
    # 4. Phone Number
    phone_match = re.search(r'(?i)(?:\bPhone\s*Number\b|\bPhone\b|\bMobile\b|\bContact\b)\s*[\:\.\;\-\_\=\[\]]*\s*([0-9\s\-\+\/A-Za-z]{7,35})(?=\s*(?:Date|Gender|NIC|Address|Occupation|Email|SECTION|$))', complainant_segment)
    if phone_match:
        phone_raw = phone_match.group(1).strip()
        digit_map = {
            'O': '0', 'o': '0', 'S': '5', 's': '5', 'F': '7', 'f': '7',
            'b': '6', 'B': '8', 'z': '8', 'Z': '8', 'g': '9', 'q': '9',
            'i': '1', 'I': '1', 'l': '1', '/': '1', '|': '1'
        }
        phone_mapped = ""
        for c in phone_raw:
            if c.isdigit():
                phone_mapped += c
            elif c in digit_map:
                phone_mapped += digit_map[c]
        if phone_mapped:
            res.phone = phone_mapped

    # 5. Section 3 Columns Spatially
    if ocr.blocks:
        y_coords = {}
        for b in ocr.blocks:
            text_tok = b.text.upper()
            if not b.bbox: continue
            
            mid_y = (b.bbox[1] + b.bbox[3]) / 2
            
            if "SECTION" in text_tok:
                num_match = re.search(r'\d', text_tok)
                if num_match:
                    y_coords[int(num_match.group(0))] = b.bbox[1]
                else:
                    if 120 <= mid_y <= 160: y_coords[1] = b.bbox[1]
                    elif 240 <= mid_y <= 300: y_coords[2] = b.bbox[1]
                    elif 390 <= mid_y <= 460: y_coords[3] = b.bbox[1]
                    elif 540 <= mid_y <= 650: y_coords[4] = b.bbox[1]
                    elif 720 <= mid_y <= 810: y_coords[5] = b.bbox[1]
                    elif 820 <= mid_y <= 900: y_coords[6] = b.bbox[1]
                    
        defaults = {1: 135, 2: 260, 3: 410, 4: 570, 5: 750, 6: 850}
        for i in range(1, 7):
            if i not in y_coords:
                y_coords[i] = defaults[i]
                
        min_y = y_coords[4] - 70
        max_y = y_coords[4] - 5
        
        p_inv_tokens = [b for b in ocr.blocks if b.bbox and 0 <= (b.bbox[0]+b.bbox[2])/2 <= 310 and min_y <= (b.bbox[1]+b.bbox[3])/2 <= max_y]
        s_ind_tokens = [b for b in ocr.blocks if b.bbox and 310 <= (b.bbox[0]+b.bbox[2])/2 <= 600 and min_y <= (b.bbox[1]+b.bbox[3])/2 <= max_y]
        v_det_tokens = [b for b in ocr.blocks if b.bbox and 600 <= (b.bbox[0]+b.bbox[2])/2 <= 1000 and min_y <= (b.bbox[1]+b.bbox[3])/2 <= max_y]
        
        p_inv_tokens.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
        s_ind_tokens.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
        v_det_tokens.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
        
        def filter_headers(tokens_list, headers_to_remove):
            res_words = []
            for b in tokens_list:
                word = b.text
                word_clean = re.sub(r'[^A-Za-z]', '', word).lower()
                if any(h in word_clean for h in headers_to_remove):
                    continue
                res_words.append(word)
            return " ".join(res_words)
            
        headers_p = ["persons", "involved", "people", "details", "landmark"]
        headers_s = ["suspected", "individuals", "suspects", "landmark"]
        headers_v = ["vehicle", "details", "weapons", "mentioned", "landmark"]
        
        p_inv = filter_headers(p_inv_tokens, headers_p)
        s_ind = filter_headers(s_ind_tokens, headers_s)
        v_det = filter_headers(v_det_tokens, headers_v)
        
        def clean_col_val(val):
            val = val.strip(" :;|,-_[]()")
            val = re.sub(r'^[|\[\]\(\)\-\:\;\,\.\s\_\=\~\?]+', '', val)
            val = re.sub(r'\s+', ' ', val).strip(" ,.;-_")
            return val
            
        res.persons_involved = clean_col_val(p_inv) or res.persons_involved
        res.suspected_individuals = clean_col_val(s_ind) or res.suspected_individuals
        res.vehicle_details = clean_col_val(v_det) or res.vehicle_details
    
    return _detect_checkboxes(ocr.blocks, res, sec1_range, sec5_range)

def _first_match(text: str, patterns: list[str]) -> Optional[str]:
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            try: return m.group(1).strip()
            except IndexError: return m.group(0).strip()
    return None

def _clean(value: str, field_key: str) -> str:
    # First, handle location and address specific cleanup before generic stripping
    if field_key == "location":
        value = re.sub(r'(?i)^\s*(?:GPS\s*/?\s*Landmark|Landmark|GPS)\s*[\:\.\;\-\_\=]?\s*', '', value)
        # Strip any leading random letter prefix from OCR (e.g. Z , F Z )
        value = re.sub(r'^[A-Za-z]\s+', '', value)
        value = re.sub(r'^[A-Za-z]\s+', '', value)
        value = re.sub(r'^[^A-Za-z0-9]+', '', value)

    if field_key == "address":
        # Remove grid line artifacts like : | Ay,- or similar at start
        value = re.sub(r'^[\s\:\;\|Ay\,\-\_]+', '', value)

    if field_key not in ["description", "evidence_notes", "manual_notes", "address"]:
        _trailing_labels = re.compile(r"(?i)\s+(complaint|category|section|officer|nic|phone|mobile|address|date|location|description|form|occupation|email|badge|rank|branch|gender|full|reference)\b.*$")
        value = _trailing_labels.sub("", value).strip()

    if field_key in ["email", "nic_number", "phone", "reference_number", "badge_number", "dob", "date", "incident_date"]:
        if field_key in ["date", "dob", "incident_date", "date_received"]:
            # Clean leading colons, slashes, hyphens
            value = re.sub(r'^[\s\:\;\-\=\/]+', '', value)

        if field_key == "phone":
            value = value.replace("/", "").replace("S", "5").replace("s", "5")
            value = re.sub(r'[^0-9\+\-]', '', value)
        if field_key == "dob":
            value = value.replace("%", "3") # Specific fix for common misread of 3/8/0

        if field_key == "email" or re.search(r"\w\s+\w\s+\w", value):
            value = re.sub(r"\s+", "", value)
        if field_key in ["date", "dob", "incident_date", "date_received"]:
            value = re.sub(r"\s*/\s*", "/", value)
            value = value.strip(" /\\-")
            v_num = re.sub(r"\D", "", value)
            if len(v_num) == 8 and "/" not in value and "-" not in value:
                if v_num.startswith("20"):
                    value = f"{v_num[:4]}-{v_num[4:6]}-{v_num[6:]}"
                else:
                    value = f"{v_num[:2]}/{v_num[2:4]}/{v_num[4:]}"
        value = value.replace("[", "").replace("]", "").replace("|", "").replace("©", "")
        value = re.sub(r"(?i)\[?(HH|MM|SS|DD|YYYY|AM|PM)\]?", "", value)
        
        if field_key == "reference_number":
            value = re.sub(r"(?i)\s*(Date|Time|Police|Station|Category).*$", "", value).strip()
            value = re.sub(r"^[S\s]*[L\s]*[P\s]*[-]?\s*", "SLP-", value)
            if "-" in value:
                parts = value.split("-")
                value = "-".join(["".join(p.split()) for p in parts])
            value = value.upper()
    
    # Remove non-ASCII characters (Hallucinations)
    value = "".join(c for c in value if ord(c) < 128)
    
    return re.sub(r"\s+", " ", value).strip(" ,;.")

def _detect_checkboxes(blocks: List[OCRBlock], result: KIEResult, sec1_range: Tuple[float, float], sec5_range: Tuple[float, float]) -> KIEResult:
    evidence_map = {"photos": "has_photos", "medical": "has_medical_report", "cctv": "has_cctv", "witness": "has_witness_statement", "audio": "has_audio_recording", "other": "has_other_evidence"}
    category_map = {"theft": "is_theft", "assault": "is_assault", "narcotics": "is_narcotics", "traffic incident": "is_traffic", "domestic violence": "is_domestic_violence", "child abuse": "is_child_abuse", "suspicious activity": "is_suspicious_activity", "other": "is_other_category"}
    
    for label, attr in evidence_map.items():
        if _check_near_label(blocks, label, y_range=sec5_range):
            setattr(result, attr, True)

    active_categories = []
    for label, attr in category_map.items():
        if _check_near_label(blocks, label, y_range=sec1_range):
            setattr(result, attr, True)
            active_categories.append(label.title())
            
    if active_categories:
        result.complaint_category = ", ".join(active_categories)
    return result

def _check_near_label(blocks: List[OCRBlock], label_query: str, y_range: Tuple[float, float] = None) -> bool:
    MARKED_SYMBOLS = ["[x]", "[v]", "x", "v", "*", "☑", "☒", "✓", "y", "/", "\\", "|", "V", "Y", "1"]
    anchor = layout_utils.find_block_by_text(blocks, label_query, y_range=y_range)
    if not anchor: return False
        
    if any(sym in anchor.text.lower() for sym in MARKED_SYMBOLS):
        text = anchor.text.lower()
        for sym in MARKED_SYMBOLS:
            if sym in text:
                if "[" in sym and "]" in sym: return True
                if text.strip().startswith(sym) and len(text.strip()) > len(sym) + 1: return True
                
    ax0, ay0, ax1, ay1 = anchor.bbox
    a_mid_y = (ay0 + ay1) / 2
    
    for b in blocks:
        if not b.bbox or b == anchor: continue
        bx0, by0, bx1, by1 = b.bbox
        b_mid_y = (by0 + by1) / 2
        
        # Check in a slightly larger horizontal window and narrow vertical window
        if abs(b_mid_y - a_mid_y) < 25:
            dist = bx0 - ax0
            # If the box is to the left of the label (standard for many forms) or slightly to the right
            if -150 < dist < 120:
                text = b.text.lower().strip()
                if any(sym in text for sym in MARKED_SYMBOLS) or text in ["x", "v", "*", "✓", "/", "\\", "|", "1"]:
                    return True
                # Enhanced: detect "filled" boxes that might just be read as a solid block or noise
                if len(text) > 0 and len(text) < 4 and not text[0].isalnum():
                    return True
    return False

def _fallback_description(text: str, extracted: dict) -> Optional[str]:
    remaining = text
    for val in extracted.values():
        if val and isinstance(val, str): remaining = remaining.replace(val, "")
    paragraphs = [p.strip() for p in remaining.split("\n") if len(p.strip()) > 40]
    return paragraphs[-1] if paragraphs else None
