"""
Hybrid KIE & Post-Processing Correction Engine for Sri Lanka Police Intake Forms.
Combines LayoutLMv3 token predictions, Bounding Box Template Anchors, 
OpenCV Checkmark Detection, and validation layers.
"""
from __future__ import annotations
import re
import os
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Tuple
from app.models.pipeline_models import KIEResult, ExtractedField, OCRResult

# 1. Coordinate-based template zones (Normalized to 0-1000 scale)
TEMPLATE_COORDINATES = {
    "reference_number": [50, 140, 320, 200],
    "form_date": [340, 140, 480, 200],
    "form_time": [500, 140, 680, 200],
    "police_station": [700, 140, 950, 200],
    "complainant_name": [150, 275, 580, 310],
    "nic_number": [680, 275, 950, 310],
    "dob": [150, 300, 360, 335],
    "phone": [680, 300, 950, 335],
    "address": [150, 335, 580, 400],
    "occupation": [680, 335, 950, 365],
    "email": [680, 365, 950, 400],
    "incident_date": [50, 460, 360, 495],
    "incident_time": [400, 460, 680, 495],
    "location": [170, 495, 580, 530],
    "landmark": [680, 495, 950, 530],
    "receiving_officer_name": [150, 840, 500, 875],
    "badge_number": [510, 840, 720, 875],
    "rank": [730, 840, 950, 875],
    "branch": [50, 875, 400, 910],
    "assigned_station": [420, 875, 720, 910],
    "date_received": [650, 910, 950, 945],
}

# OpenCV Checkbox Mapping (Normalized [x_min, y_min, x_max, y_max])
CHECKBOX_COORDINATES = {
    # Complaint Categories (Section 1)
    "is_theft": [230, 215, 255, 235],
    "is_assault": [380, 215, 405, 235],
    "is_domestic_violence": [550, 215, 575, 235],
    "is_suspicious_activity": [740, 215, 765, 235],
    "is_narcotics": [230, 235, 255, 255],
    "is_traffic": [385, 235, 410, 255],
    "is_child_abuse": [550, 235, 575, 255],
    "is_other_category": [740, 235, 765, 255],
    # Gender (Section 2)
    "gender_male": [435, 320, 460, 340],
    "gender_female": [512, 320, 537, 340],
    # Evidence Types (Section 5)
    "has_photos": [30, 785, 55, 805],
    "has_witness_statement": [240, 785, 265, 805],
    "has_medical_report": [30, 805, 55, 825],
    "has_audio_recording": [240, 805, 265, 825],
    "has_cctv": [30, 825, 55, 845],
    "has_other_evidence": [240, 825, 265, 845],
}

LABEL_RULES = {
    "is_theft": {"word": "Theft", "offset": (-32, -7), "y_range": (150, 300), "x_range": (200, 350)},
    "is_assault": {"word": "Assault", "offset": (-28, -3), "y_range": (150, 300), "x_range": (350, 500)},
    "is_domestic_violence": {"word": "Domestic", "offset": (-31, -6), "y_range": (150, 300), "x_range": (500, 700)},
    "is_suspicious_activity": {"word": "Suspicious", "offset": (-30, -5), "y_range": (150, 300), "x_range": (700, 900)},
    "is_narcotics": {"word": "Narcotics", "offset": (-33, -8), "y_range": (200, 300), "x_range": (200, 350)},
    "is_traffic": {"word": "Traffic", "offset": (-23, -3), "y_range": (200, 300), "x_range": (350, 500)},
    "is_child_abuse": {"word": "Child", "offset": (-31, -6), "y_range": (200, 300), "x_range": (500, 700)},
    "is_other_category": {"word": "Other", "offset": (-30, -5), "y_range": (200, 300), "x_range": (700, 900)},
    "gender_male": {"word": "Male", "offset": (-30, -5), "y_range": (300, 380), "x_range": (400, 500)},
    "gender_female": {"word": "Female", "offset": (-34, -9), "y_range": (300, 380), "x_range": (500, 650)},
    "has_photos": {"word": "Photos", "offset": (-40, -15), "y_range": (750, 850), "x_range": (0, 200)},
    "has_witness_statement": {"word": "Witness", "offset": (-37, -12), "y_range": (750, 850), "x_range": (200, 450)},
    "has_medical_report": {"word": "Medical", "offset": (-34, -9), "y_range": (790, 860), "x_range": (0, 200)},
    "has_audio_recording": {"word": "Audio", "offset": (-37, -12), "y_range": (790, 860), "x_range": (200, 450)},
    "has_cctv": {"word": "CCTV", "offset": (-38, -13), "y_range": (810, 880), "x_range": (0, 200)},
    "has_other_evidence": {"word": "Other", "offset": (-37, -12), "y_range": (810, 880), "x_range": (200, 450)},
}

def get_checkbox_bbox(box_name: str, tokens: List[Dict[str, Any]]) -> List[float]:
    """
    Dynamically locate the checkbox bbox relative to its OCR label.
    """
    rule = LABEL_RULES.get(box_name)
    if not rule:
        return CHECKBOX_COORDINATES.get(box_name, [0, 0, 0, 0])
        
    target_word = rule["word"].lower()
    min_y, max_y = rule["y_range"]
    min_x, max_x = rule["x_range"]
    offset_min, offset_max = rule["offset"]
    
    matching_token = None
    for t in tokens:
        text = t.get("text", "").strip().lower()
        text = text.strip(" :;|,-_[]()")
        bbox = t.get("bbox", [0, 0, 0, 0])
        
        if target_word in text and min_y <= bbox[1] <= max_y and min_x <= bbox[0] <= max_x:
            matching_token = t
            break
            
    if matching_token:
        bbox = matching_token["bbox"]
        x_min = max(0, bbox[0] + offset_min)
        x_max = min(1000, bbox[0] + offset_max)
        y_min = max(0, bbox[1] - 5)
        y_max = min(1000, bbox[3] + 5)
        
        center_y = (y_min + y_max) // 2
        y_min = max(0, center_y - 10)
        y_max = min(1000, center_y + 10)
        
        return [x_min, y_min, x_max, y_max]
        
    return CHECKBOX_COORDINATES.get(box_name, [0, 0, 0, 0])

# --- OpenCV Box Cleaner & Checkbox Analyzer ---

def detect_visual_checkmark(
    img_path: str, 
    bbox: List[float], 
    threshold_pct: float = 6.0, 
    tokens: List[Dict[str, Any]] = None, 
    box_name: str = None
) -> bool:
    """
    Check if a checkbox is ticked using image binarization, dynamic label-relative matching, 
    and contour-based inner region density checking.
    """
    if tokens and box_name:
        bbox = get_checkbox_bbox(box_name, tokens)

    img = cv2.imread(img_path)
    if img is None:
        return False
    
    img_h, img_w = img.shape[:2]
    # Denormalize bounding box
    x0 = int((bbox[0] / 1000) * img_w)
    y0 = int((bbox[1] / 1000) * img_h)
    x1 = int((bbox[2] / 1000) * img_w)
    y1 = int((bbox[3] / 1000) * img_h)
    
    crop = img[y0:y1, x0:x1]
    if crop.size == 0:
        return False
        
    # Convert to grayscale and threshold
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    
    # Exclude outer border using contour detection
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return False
        
    # Find largest contour (should be the checkbox box)
    largest_contour = max(contours, key=cv2.contourArea)
    x_b, y_b, w_b, h_b = cv2.boundingRect(largest_contour)
    
    # Verify contour looks like a checkbox
    if w_b < 10 or h_b < 10:
        # Fallback to static margin if contour is too small
        margin = 3
        inner_crop = thresh[margin:-margin, margin:-margin]
    else:
        # Shrink by 3 pixels from the detected checkbox border
        pad_x = min(3, w_b // 4)
        pad_y = min(3, h_b // 4)
        inner_crop = thresh[y_b + pad_y : y_b + h_b - pad_y, x_b + pad_x : x_b + w_b - pad_x]
        
    if inner_crop.size == 0:
        return False
        
    total_pixels = inner_crop.size
    non_zero = cv2.countNonZero(inner_crop)
    fill_ratio = (non_zero / total_pixels) * 100
    
    return fill_ratio > threshold_pct

def remove_form_gridlines(image_path: str, output_path: str):
    """
    Remove vertical and horizontal gridlines from intake form so Tesseract only sees ink.
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # Remove horizontal lines
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    remove_horiz = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horiz_kernel, iterations=2)
    cnts = cv2.findContours(remove_horiz, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(img, [c], -1, (255, 255, 255), 3)

    # Remove vertical lines
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    remove_vert = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vert_kernel, iterations=2)
    cnts = cv2.findContours(remove_vert, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(img, [c], -1, (255, 255, 255), 3)
        
    cv2.imwrite(output_path, img)

# --- Heuristic Parsing & Data Validation Layers ---

def clean_ocr_text(val: str, field_key: str) -> str:
    """
    Validation and sanitation layer for specific fields.
    """
    if not val:
        return ""
    
    # Strip layout punctuation and bracket/box labels
    val = val.strip(" :;|,-_[]()")
    val = "".join(c for c in val if ord(c) < 128) # strip non-ASCII
    
    if field_key == "reference_number":
        val = re.sub(r'\s+', '', val).replace("=", "-").replace("5", "S").replace("1", "L")
        val = re.sub(r'^[S]*[L]*[P]*-?', 'SLP-', val)
        val = val.upper()
        
    elif field_key in ["dob", "form_date", "incident_date", "date_received"]:
        # Handle digit OCR misreads (common: 9 mistook as 7 or %; 0 mistook as %)
        val = val.replace("%", "0").replace("&", "0")
        val = re.sub(r'[^0-9/]', '', val)
        val = re.sub(r'\s*/\s*', '/', val)
        # Reconstruct standard date format: DD/MM/YYYY
        nums = re.sub(r'\D', '', val)
        if len(nums) == 8:
            val = f"{nums[:2]}/{nums[2:4]}/{nums[4:]}"
            
    elif field_key in ["phone"]:
        val = val.replace("S", "5").replace("s", "5").replace("/", "")
        val = re.sub(r'[^0-9]', '', val)
        if len(val) == 9 and not val.startswith("0"):
            val = "0" + val
            
    elif field_key == "email":
        # Strip all whitespace often inserted by handwriting tokenisers
        val = re.sub(r'\s+', '', val)
        
    elif field_key == "nic_number":
        val = re.sub(r'\s+', '', val).upper()
        # Sri Lankan old format NIC support (e.g. 950034765V)
        if len(val) == 10 and (val.endswith("V") or val.endswith("X")):
            pass
        # Sri Lankan new format NIC support (12 digits)
        elif len(val) == 12 and val.isdigit():
            pass
            
    return re.sub(r'\s+', ' ', val).strip()

def filter_tokens_by_coordinates(tokens: List[Dict[str, Any]], target_bbox: List[int]) -> str:
    """
    Extract words directly falling within the template coordinates.
    """
    matched_words = []
    # target_bbox: [x0, y0, x1, y1]
    tx0, ty0, tx1, ty1 = target_bbox
    
    # Sort tokens primarily by reading order (Y coordinate, then X coordinate)
    sorted_tokens = sorted(tokens, key=lambda t: (t.get("bbox", [0,0,0,0])[1], t.get("bbox", [0,0,0,0])[0]))
    
    for token in sorted_tokens:
        bbox = token.get("bbox")
        if not bbox:
            continue
        bx0, by0, bx1, by1 = bbox
        
        # Calculate overlap center
        bcx = (bx0 + bx1) / 2
        bcy = (by0 + by1) / 2
        
        # If token falls inside coordinate boundaries
        if tx0 <= bcx <= tx1 and ty0 <= bcy <= ty1:
            matched_words.append(token.get("text", ""))
            
    return " ".join(matched_words)

# --- Integrated Extractor Run ---

def extract_form_hybrid(image_path: str, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main orchestrator combining Coordinate Filtering, Checkbox Checking, and Validation.
    """
    results = {}
    
    # 1. Coordinate-based text extraction (Static fields)
    for field_name, bbox in TEMPLATE_COORDINATES.items():
        raw_val = filter_tokens_by_coordinates(tokens, bbox)
        results[field_name] = clean_ocr_text(raw_val, field_name)
        
    # 2. OpenCV Checkbox Validation
    checkbox_results = {}
    for box_name, bbox in CHECKBOX_COORDINATES.items():
        checkbox_results[box_name] = detect_visual_checkmark(image_path, bbox)
        
    # 3. Resolve Gender Checkboxes
    gender = None
    if checkbox_results.get("gender_female"):
        gender = "Female"
    elif checkbox_results.get("gender_male"):
        gender = "Male"
    results["gender"] = gender
    
    # 4. Inject Checkbox Values
    results.update(checkbox_results)
    
    return results
