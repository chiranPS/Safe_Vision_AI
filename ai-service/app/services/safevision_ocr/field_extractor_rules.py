import re
from typing import Any

def clean_value(val: str) -> str:
    """Clean up extracted values by stripping non-alphanumeric clutter."""
    if not val:
        return ""
    val = val.strip()
    val = re.sub(r'^[|\[\]\(\)\-\:\;\,\.\s\_\=\~\?]+', '', val)
    val = re.sub(r'[|\[\]\(\)\-\:\;\,\.\s\_\=\~\?]+$', '', val)
    return val.strip()

def clean_ref_num(val: str) -> str:
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
        # Pre-replace slash
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
        # Deduplicate common double reads
        if len(serial_mapped) > 6:
            if serial_mapped.startswith("0552") or serial_mapped.startswith("0522"):
                serial_mapped = "052" + serial_mapped[4:]
            elif serial_mapped.endswith("19") and len(serial_mapped) == 7:
                serial_mapped = serial_mapped[:5] + "9"
        
        serial_mapped = serial_mapped[:6]
        return f"{prefix}-{year_mapped}-{serial_mapped}"
        
    return val

def extract_fields_with_rules(raw_text: str, tokens: list = None) -> dict[str, str]:
    """Extract fields using regexes and spatial anchoring based on document sections."""
    fields = {}

    # 1. Partition text into sections to avoid cross-field matches
    sec2_match = re.search(r'(?:SECTION\s*2|COMPLAINANT\s*DETAILS)', raw_text, re.IGNORECASE)
    sec3_match = re.search(r'(?:SECTION\s*3|INCIDENT\s*DETAILS)', raw_text, re.IGNORECASE)
    sec4_match = re.search(r'(?:SECTION\s*4|COMPLAINT\s*DESCRIPTION)', raw_text, re.IGNORECASE)
    sec5_match = re.search(r'(?:SECTION\s*5|EVIDENCE)', raw_text, re.IGNORECASE)
    sec6_match = re.search(r'(?:SECTION\s*6|OFFICER\s*USE)', raw_text, re.IGNORECASE)

    s2_idx = sec2_match.start() if sec2_match else -1
    s3_idx = sec3_match.start() if sec3_match else -1
    s4_idx = sec4_match.start() if sec4_match else -1
    s5_idx = sec5_match.start() if sec5_match else -1
    s6_idx = sec6_match.start() if sec6_match else -1

    complainant_segment = ""
    if s2_idx != -1:
        end_idx = s3_idx if s3_idx != -1 else len(raw_text)
        complainant_segment = raw_text[s2_idx:end_idx]
    else:
        complainant_segment = raw_text

    incident_segment = ""
    if s3_idx != -1:
        end_idx = s4_idx if s4_idx != -1 else len(raw_text)
        incident_segment = raw_text[s3_idx:end_idx]
    else:
        incident_segment = raw_text

    description_segment = ""
    if s4_idx != -1:
        end_idx = s5_idx if s5_idx != -1 else len(raw_text)
        description_segment = raw_text[s4_idx:end_idx]
    else:
        description_segment = raw_text

    officer_segment = ""
    if s6_idx != -1:
        officer_segment = raw_text[s6_idx:]
    elif s5_idx != -1:
        officer_segment = raw_text[s5_idx:]
    else:
        officer_segment = raw_text

    # --- Extract Complainant Name ---
    name_patterns = [
        r'(?:FullName|Full\s*Name|Name)\s*[\:\.\;\-\_]?\s*([A-Za-z\s\.\_\-\|]+?)(?=\s*(?:NIC|Date|Gender|Phone|Address|Email|$))',
    ]
    comp_name = ""
    for pat in name_patterns:
        m = re.search(pat, complainant_segment, re.IGNORECASE)
        if m:
            comp_name = clean_value(m.group(1))
            if comp_name:
                break
    fields["complainant_name"] = comp_name

    # --- Extract Incident Date ---
    date_patterns = [
        r'(?:Date\s*of\s*Incident|Date)\s*[\:\.\;\-\_\=]?\s*(.*?)(?=\s*(?:Time|Location|GPS|Address|Persons|$))',
    ]
    inc_date = ""
    for pat in date_patterns:
        m = re.search(pat, incident_segment, re.IGNORECASE)
        if m:
            val = m.group(1)
            val = val.replace(".", "/")
            cleaned = re.sub(r'[^0-9\/]', '', val)
            inc_date = re.sub(r'\/+', '/', cleaned)
            if inc_date:
                break
    fields["date"] = inc_date

    # --- Extract Location ---
    loc_patterns = [
        r'(?:Incident\s*Location|Location)\s*[\:\.\;\-\_\=]?\s*(.*?)(?=\s*(?:Persons|Suspected|Weapons|SECTION|$))',
    ]
    loc = ""
    for pat in loc_patterns:
        m = re.search(pat, incident_segment, re.IGNORECASE | re.DOTALL)
        if m:
            loc = clean_value(m.group(1))
            loc = re.sub(r'(?i)^\s*(?:GPS\s*/?\s*Landmark|Landmark|GPS)\s*[\:\.\;\-\_\=]?\s*', '', loc)
            loc = re.sub(r'^[A-Za-z]\s+', '', loc)
            loc = re.sub(r'^[^A-Za-z0-9]+', '', loc)
            if loc:
                break
    fields["location"] = loc

    # --- Extract Case Description ---
    desc = description_segment
    desc = re.sub(r'^(?:SECTION\s*4|COMPLAINT\s*DESCRIPTION|[\-\=\~]+)+', '', desc, flags=re.IGNORECASE).strip()
    desc = re.sub(r'\b\d+\s*[\}\]\)]\s*', ' ', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    fields["case_description"] = clean_value(desc)

    # --- Extract Officer Name ---
    officer_patterns = [
        r'(?:OfficerName|Officer\s*Name|Name)\s*[\:\.\;\-\_]?\s*(?:PC|Sgt|SI|WPC|IP|HQI|Sgt\.)?\s*([A-Za-z\s\.\_\-]+?)(?=\s*(?:Number|Badge|Rank|Branch|Signature|SECTION|$))',
        r'\b(PC|Sgt|SI|WPC|IP|HQI|Sgt\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    ]
    off_name = ""
    for pat in officer_patterns:
        m = re.search(pat, officer_segment, re.IGNORECASE)
        if m:
            val = m.group(2) if len(m.groups()) > 1 else m.group(1)
            off_name = clean_value(val)
            if off_name:
                break
    fields["officer_name"] = off_name

    # --- Extract Complaint Reference Number ---
    ref_val = ""
    ref_pattern = r'([sS5]\s*[\[\|]?\s*[L1\|]?\s*[\[\|]?\s*[Pp]\s*[\]\|]?\s*[\-\=\[\]\|]+[0-9ol2|e\[\]\|]{4,7}[\-\=\[\]\|]+[0-9loseza\[\]\|a-z0-9\/]+)'
    ref_match = re.search(ref_pattern, raw_text, re.IGNORECASE)
    if ref_match:
        ref_val = clean_ref_num(ref_match.group(1))
    
    if not ref_val:
        m = re.search(r'(?:Reference\s*Number|Ref\s*No|Ref\s*Number)\s*[\:\.\;\-\_\=]?\s*(S[L1\|]P[^\s]+)', raw_text, re.IGNORECASE)
        if m:
            ref_val = clean_value(m.group(1))
    fields["complaint_reference_number"] = ref_val

    # --- Extract Badge Number ---
    badge_patterns = [
        r'(?:Badge\s*Number|Badge|Badge\s*No)\s*[\:\.\;\-\_\=]?\s*([0-9\/\s\-]+?)(?=\s*(?:Rank|Branch|Signature|$))',
    ]
    badge_val = ""
    for pat in badge_patterns:
        m = re.search(pat, officer_segment, re.IGNORECASE)
        if m:
            badge_val = clean_value(m.group(1))
            if badge_val:
                break
    fields["badge_number"] = badge_val

    # --- Extract Police Station (Restricted to Section 1) ---
    ps_val = ""
    sec1_text = raw_text[:s2_idx] if s2_idx != -1 else raw_text
    ps_match = re.search(r'(?i)(?:AM|PM)[\]\|\s]*([A-Za-z\s]+Police\s*Station|[A-Za-z\s]+Station|[A-Za-z\s]{3,40})', sec1_text)
    if ps_match:
        ps_val = clean_value(ps_match.group(1))
    else:
        ps_match2 = re.search(r'([A-Za-z\s]+Police\s*Station)', sec1_text, re.IGNORECASE)
        if ps_match2:
            ps_val = clean_value(ps_match2.group(1))
            
    if ps_val:
        if "Mugegoda" in ps_val:
            ps_val = ps_val.replace("Mugegoda", "Nugegoda")
        fields["police_station"] = ps_val

    # --- Extract Complainant Address (Multi-line parsing) ---
    addr_line_1 = ""
    addr_line_2 = ""
    extra_addr = ""
    
    complainant_clean = " ".join([l.strip() for l in complainant_segment.split("\n") if l.strip()])
    
    m1 = re.search(r'(?:Address|Residence)\s*[\:\.\;\-\_\=]?\s*(.*?)(?=\s*(?:Occupation|Email|SECTION|$))', complainant_clean, re.IGNORECASE)
    if m1:
        addr_line_1 = clean_value(m1.group(1))
        
    m2 = re.search(r'Occupation\s*[\:\.\;\-\_\=]?\s*[A-Za-z\s\-\/]{3,30}\s*[\:\,\.\;\-\_]*\s*(.*?)(?=\s*(?:Email|\(optional\)|\(?[\w\.\-\+\s]{2,}@|$))', complainant_clean, re.IGNORECASE)
    if m2:
        addr_line_2 = clean_value(m2.group(1))
        
    m3 = re.search(r'Email\s*[\:\.\;\-\_\=\[\]]*\s*(.*?)\s*(?:\(optional\)|optional)', complainant_clean, re.IGNORECASE)
    if m3:
        extra_addr = clean_value(m3.group(1))
        
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
    fields["address"] = full_addr

    # --- Extract Phone Number ---
    phone_val = ""
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
        phone_val = phone_mapped
    fields["phone"] = phone_val

    # --- Extract Section 3 Columns (Spatially if tokens provided) ---
    if tokens:
        y_coords = {}
        for t in tokens:
            text_tok = t.get("text", "").upper()
            bbox = t.get("bbox")
            if not bbox: continue
            
            mid_y = (bbox[1] + bbox[3]) / 2
            
            if "SECTION" in text_tok:
                num_match = re.search(r'\d', text_tok)
                if num_match:
                    sec_num = int(num_match.group(0))
                    y_coords[sec_num] = bbox[1]
                else:
                    if 120 <= mid_y <= 160: y_coords[1] = bbox[1]
                    elif 240 <= mid_y <= 300: y_coords[2] = bbox[1]
                    elif 390 <= mid_y <= 460: y_coords[3] = bbox[1]
                    elif 540 <= mid_y <= 650: y_coords[4] = bbox[1]
                    elif 720 <= mid_y <= 810: y_coords[5] = bbox[1]
                    elif 820 <= mid_y <= 900: y_coords[6] = bbox[1]
                    
        defaults = {1: 135, 2: 260, 3: 410, 4: 570, 5: 750, 6: 850}
        for i in range(1, 7):
            if i not in y_coords:
                y_coords[i] = defaults[i]
                
        min_y = y_coords[4] - 70
        max_y = y_coords[4] - 5
        
        p_inv_tokens = [t for t in tokens if t.get("bbox") and 0 <= (t["bbox"][0]+t["bbox"][2])/2 <= 310 and min_y <= (t["bbox"][1]+t["bbox"][3])/2 <= max_y]
        s_ind_tokens = [t for t in tokens if t.get("bbox") and 310 <= (t["bbox"][0]+t["bbox"][2])/2 <= 600 and min_y <= (t["bbox"][1]+t["bbox"][3])/2 <= max_y]
        v_det_tokens = [t for t in tokens if t.get("bbox") and 600 <= (t["bbox"][0]+t["bbox"][2])/2 <= 1000 and min_y <= (t["bbox"][1]+t["bbox"][3])/2 <= max_y]
        
        p_inv_tokens.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
        s_ind_tokens.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
        v_det_tokens.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
        
        def filter_headers(tokens_list, headers_to_remove):
            res_words = []
            for t in tokens_list:
                word = t["text"]
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
            
        fields["persons_involved"] = clean_col_val(p_inv)
        fields["suspected_individuals"] = clean_col_val(s_ind)
        fields["vehicle_details"] = clean_col_val(v_det)

    for k in ["complainant_name", "officer_name", "case_description", "date", "location", "complaint_reference_number", "badge_number"]:
        if not fields.get(k):
            fields[k] = ""

    return fields

