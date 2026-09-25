"""
Legacy OCR service (used by /ocr/process route).
Migrated from PaddleOCR to EasyOCR for Python 3.13 Windows compatibility.
"""
import asyncio
import logging
from pathlib import Path

import cv2
import numpy as np

from ..models.ocr_models import OCRResponse

logger = logging.getLogger(__name__)

# ── Singleton ─────────────────────────────────────────────────────────────────
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        try:
            import easyocr
            _engine = easyocr.Reader(["en"], gpu=False, verbose=False)
            logger.info("EasyOCR (legacy route) engine ready.")
        except Exception as exc:
            logger.warning(f"EasyOCR unavailable: {exc}")
    return _engine


# ── Public entry-point ────────────────────────────────────────────────────────

async def process_document(file_path: Path, filename: str) -> OCRResponse:
    engine = _get_engine()

    if engine is None:
        await asyncio.sleep(0)
        return OCRResponse(
            rawText=f"[MOCK] Report received: {filename}.\nFallback text extraction.",
            confidenceScore=0.92,
        )

    suffix = file_path.suffix.lower()
    loop = asyncio.get_event_loop()

    try:
        if suffix == ".pdf":
            raw_text, confidence = await loop.run_in_executor(
                None, _process_pdf, engine, str(file_path)
            )
        elif suffix in (".jpg", ".jpeg", ".png"):
            raw_text, confidence = await loop.run_in_executor(
                None, _process_image, engine, str(file_path)
            )
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        return OCRResponse(
            rawText=raw_text.strip(),
            confidenceScore=round(confidence, 4),
        )
    except Exception as exc:
        logger.error(f"OCR error on {filename}: {exc}")
        raise


# ── Handlers ──────────────────────────────────────────────────────────────────

def _process_image(engine, image_path: str) -> tuple[str, float]:
    results = engine.readtext(image_path, detail=1, paragraph=False)
    return _parse(results)


def _process_pdf(engine, pdf_path: str) -> tuple[str, float]:
    import fitz
    doc = fitz.open(pdf_path)
    all_text, all_conf = [], []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        img_bgr = (
            cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR) if pix.n == 4
            else cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) if pix.n == 3
            else cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
        )
        results = engine.readtext(img_bgr, detail=1, paragraph=False)
        text, conf = _parse(results)
        if text:
            all_text.append(text)
            all_conf.append(conf)

    doc.close()
    combined_conf = sum(all_conf) / len(all_conf) if all_conf else 0.0
    return "\n".join(all_text), combined_conf


def _parse(results) -> tuple[str, float]:
    """Parse EasyOCR [(bbox, text, conf)] output."""
    if not results:
        return "", 0.0
    texts = [r[1].strip() for r in results if r[1].strip()]
    confs = [r[2] for r in results if r[1].strip()]
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return "\n".join(texts), avg_conf
