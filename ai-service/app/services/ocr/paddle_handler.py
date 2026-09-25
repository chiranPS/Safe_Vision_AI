"""
PaddleOCR Stage — High-accuracy text extraction.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from ...models.pipeline_models import OCRBlock

logger = logging.getLogger(__name__)

# Singleton engine
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        import os
        os.environ['FLAGS_enable_pir_api'] = '0'
        os.environ['FLAGS_enable_pir_in_executor'] = '0'
        os.environ['FLAGS_use_mkldnn'] = '0'
        os.environ['FLAGS_use_onednn'] = '0'
        os.environ['FLAGS_enable_new_executor'] = '0'
        os.environ['PADDLE_PIR_ENABLE'] = '0'
        os.environ['PADDLE_PIR_MODE'] = '0'
        
        # 1. Try PaddleOCR (High Accuracy)
        try:
            from paddleocr import PaddleOCR
            import logging as py_logging
            py_logging.getLogger("ppocr").setLevel(py_logging.WARNING)
            # Removed show_log=False to avoid 'Unknown argument' error
            _engine = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info("PaddleOCR engine initialised successfully.")
            return ("paddle", _engine)
        except Exception as exc:
            logger.warning(f"PaddleOCR unavailable: {exc}")
            
        # 2. Try Docling (Robust Fallback - already in venv)
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False 
            _engine = DocumentConverter(pipeline_options=pipeline_options)
            logger.info("Docling engine initialised for OCR fallback (Optimised).")
            return ("docling", _engine)
        except Exception as exc:
            logger.warning(f"Docling also unavailable: {exc}")

        # 3. Last resort EasyOCR
        try:
            import easyocr
            _engine = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("EasyOCR engine initialised successfully.")
            return ("easy", _engine)
        except Exception as exc:
            logger.warning(f"EasyOCR also unavailable: {exc}")
            
    if _engine:
        mod_name = getattr(_engine, "__module__", "").lower()
        if "paddle" in mod_name: return "paddle", _engine
        if "docling" in mod_name: return "docling", _engine
        return "easy", _engine
    return None, None

def extract_text(file_path: Path) -> Tuple[List[OCRBlock], int]:
    """
    Synchronous extraction logic.
    """
    engine_type, engine = _get_engine()
    if not engine:
        return [], 0

    suffix = file_path.suffix.lower()
    
    try:
        if engine_type == "paddle":
            if suffix == '.pdf':
                return _process_pdf_paddle(engine, str(file_path))
            else:
                return _process_image_paddle(engine, str(file_path))
        elif engine_type == "docling":
            if suffix == '.pdf':
                return _process_pdf_docling(engine, str(file_path))
            else:
                return _process_image_docling(engine, str(file_path))
        else:
            # EasyOCR
            if suffix == '.pdf':
                return _process_pdf_easy(engine, str(file_path))
            else:
                return _process_image_easy(engine, str(file_path))
    except Exception as exc:
        logger.warning(f"Engine {engine_type} failed during inference: {exc}. Falling back to Docling...")
        # Fallback logic: if paddle failed, try docling, etc.
        if engine_type == "paddle":
            try:
                from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption
                from docling.datamodel.base_models import InputFormat
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = True 
                
                docling_engine = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
                        InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options)
                    }
                )
                
                logger.info(f"Running Docling fallback for {file_path}")
                if suffix == '.pdf':
                    return _process_pdf_docling(docling_engine, str(file_path))
                else:
                    return _process_image_docling(docling_engine, str(file_path))
            except Exception as d_exc:
                logger.error(f"Docling fallback also failed: {d_exc}")
        return [], 0

def _process_image_docling(engine, image_path: str, page: int = 0) -> Tuple[List[OCRBlock], int]:
    result = engine.convert(image_path)
    blocks = []
    
    # Try multiple ways to get text if one fails
    elements = []
    if hasattr(result.document, "texts") and result.document.texts:
        elements = result.document.texts
    elif hasattr(result.document, "body") and hasattr(result.document.body, "texts"):
        elements = result.document.body.texts
        
    for element in elements:
        text = element.text
        if not text or len(text.strip()) < 1: continue
        
        bbox = None
        if hasattr(element, "prov") and element.prov:
            prov = element.prov[0]
            if hasattr(prov, "bbox"):
                b = prov.bbox
                bbox = [float(b.l), float(b.t), float(b.r), float(b.b)]
        
        blocks.append(OCRBlock(
            text=text.strip(),
            confidence=0.95, # Docling OCR is usually high confidence if it works
            type=getattr(element, "label", "text") or "text",
            bbox=bbox,
            page=page
        ))
    
    # If blocks still empty, try markdown export as last resort
    if not blocks:
        md = result.document.export_to_markdown()
        if md:
            blocks.append(OCRBlock(text=md, confidence=0.8, type="markdown", bbox=None, page=page))

    return blocks, 1

def _process_pdf_docling(engine, pdf_path: str) -> Tuple[List[OCRBlock], int]:
    result = engine.convert(pdf_path)
    blocks = []
    for element in result.document.texts:
        text = element.text
        page_no = (element.prov[0].page_no - 1) if hasattr(element, "prov") and element.prov else 0
        blocks.append(OCRBlock(
            text=text.strip(),
            confidence=0.9,
            type=element.label or "text",
            bbox=None, # Simplifying for now
            page=page_no
        ))
    return blocks, result.document.num_pages if hasattr(result.document, "num_pages") else 1

def _process_image_paddle(engine, image_path: str, page: int = 0) -> Tuple[List[OCRBlock], int]:
    result = engine.ocr(image_path)
    return _parse_paddle_result(result, page), 1

def _process_image_easy(engine, image_path: str, page: int = 0) -> Tuple[List[OCRBlock], int]:
    results = engine.readtext(image_path, detail=1)
    blocks = []
    for (bbox, text, conf) in results:
        # bbox is [[x0,y0], [x1,y0], [x1,y1], [x0,y1]]
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        blocks.append(OCRBlock(
            text=text.strip(),
            confidence=conf,
            type="text",
            bbox=[min(xs), min(ys), max(xs), max(ys)],
            page=page
        ))
    return blocks, 1

def _process_pdf_paddle(engine, pdf_path: str) -> Tuple[List[OCRBlock], int]:
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    all_blocks = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        if pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
            
        result = engine.ocr(img_bgr)
        all_blocks.extend(_parse_paddle_result(result, page_num))
        
    doc.close()
    return all_blocks, len(doc)

def _process_pdf_easy(engine, pdf_path: str) -> Tuple[List[OCRBlock], int]:
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    all_blocks = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        if pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
            
        blocks, _ = _process_image_easy(engine, img_bgr, page_num)
        all_blocks.extend(blocks)
        
    doc.close()
    return all_blocks, len(doc)

def _parse_paddle_result(result, page: int) -> List[OCRBlock]:
    blocks = []
    if not result or not result[0]:
        return blocks
        
    for line in result[0]:
        box_points, (text, conf) = line[0], line[1]
        xs = [p[0] for p in box_points]
        ys = [p[1] for p in box_points]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
        blocks.append(OCRBlock(
            text=text.strip(),
            confidence=conf,
            type="text",
            bbox=bbox,
            page=page
        ))
    return blocks
