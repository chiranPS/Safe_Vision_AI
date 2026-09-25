import logging
from typing import List, Optional, Tuple
from ...models.pipeline_models import OCRBlock

logger = logging.getLogger(__name__)

def find_block_by_text(blocks: List[OCRBlock], query: str, fuzzy: bool = True, y_range: Tuple[float, float] = None) -> Optional[OCRBlock]:
    """Find an OCR block that matches or contains the query text, optionally within a Y-coordinate range."""
    query = query.lower().strip()
    for block in blocks:
        if not block.bbox: continue
        
        # Check Y-range if provided
        if y_range:
            by0, by1 = block.bbox[1], block.bbox[3]
            mid_y = (by0 + by1) / 2
            if not (y_range[0] <= mid_y <= y_range[1]):
                continue
                
        text = block.text.lower().strip()
        if fuzzy:
            if query in text:
                return block
        else:
            if query == text:
                return block
    return None

def get_text_to_right(blocks: List[OCRBlock], anchor: OCRBlock, max_dist: float = 500.0, y_tolerance: float = 20.0, boundary_labels: List[str] = None) -> str:
    """
    Get text that is physically to the right of the anchor block on the same line.
    If boundary_labels is provided, stops if it encounters a block containing any of those labels.
    """
    anchor_bbox = anchor.bbox # [x0, y0, x1, y1]
    if not anchor_bbox: return ""
    
    ax0, ay0, ax1, ay1 = anchor_bbox
    a_mid_y = (ay0 + ay1) / 2
    
    candidates = []
    
    # 1. Identify potential boundary blocks
    boundary_x = ax1 + max_dist
    if boundary_labels:
        for b in blocks:
            if b == anchor or not b.bbox: continue
            bx0, by0, bx1, by1 = b.bbox
            b_mid_y = (by0 + by1) / 2
            
            if abs(b_mid_y - a_mid_y) < y_tolerance and bx0 > ax1:
                if any(label.lower() in b.text.lower() for label in boundary_labels):
                    if bx0 < boundary_x:
                        boundary_x = bx0
    
    # 2. Collect text within anchor and boundary
    for block in blocks:
        if block == anchor or not block.bbox: continue
        
        bx0, by0, bx1, by1 = block.bbox
        b_mid_y = (by0 + by1) / 2
        
        # Is it to the right and before boundary?
        if bx0 >= ax0 - 5 and bx0 < boundary_x:
            # Is it on the same horizontal line?
            if abs(b_mid_y - a_mid_y) < y_tolerance:
                # Is it after the anchor?
                if bx0 >= ax1 - 10:
                    candidates.append((bx0, block.text))
    
    # Sort by X position and join
    candidates.sort()
    return " ".join([c[1] for c in candidates]).strip()

def get_text_below(blocks: List[OCRBlock], anchor: OCRBlock, max_dist: float = 100.0, x_tolerance: float = 50.0) -> str:
    """Get text that is physically below the anchor block."""
    anchor_bbox = anchor.bbox
    if not anchor_bbox: return ""
    
    ax0, ay0, ax1, ay1 = anchor_bbox
    a_mid_x = (ax0 + ax1) / 2
    
    candidates = []
    for block in blocks:
        if block == anchor or not block.bbox: continue
        
        bx0, by0, bx1, by1 = block.bbox
        b_mid_x = (bx0 + bx1) / 2
        
        # 1. Is it below?
        if by0 >= ay1 - 5:
            # 2. Is it aligned vertically?
            if abs(b_mid_x - a_mid_x) < x_tolerance:
                # 3. Is it within range?
                dist = by0 - ay1
                if 0 <= dist <= max_dist:
                    candidates.append((by0, block.text))
                    
    candidates.sort()
    return " ".join([c[1] for c in candidates]).strip()
