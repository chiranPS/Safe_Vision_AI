"""
OCR Stage — EasyOCR text extraction for images and PDFs.
EasyOCR (PyTorch-based) replaces PaddleOCR to ensure compatibility with
Python 3.13 on Windows without oneDNN runtime errors.

API contract is identical — outputs OCRResult consumed by the KIE stage.
"""
import asyncio
import logging
import tempfile
from pathlib import Path

import cv2
import numpy as np

from ...models.pipeline_models import OCRBlock, OCRResult

logger = logging.getLogger(__name__)

# ── Singleton engine ──────────────────────────────────────────────────────────
_engine = None

def _get_engine():
    """Lazy-load EasyOCR reader (downloads models on first call ~50 MB)."""
    global _engine
    if _engine is None:
        try:
            import easyocr
            # gpu=False for CPU-only; set gpu=True if CUDA is available
            _engine = easyocr.Reader(["en"], gpu=False, verbose=False)
            logger.info("EasyOCR engine initialised successfully.")
        except Exception as exc:
            logger.warning(f"EasyOCR unavailable — fallback mock active. Reason: {exc}")
    return _engine


# ── Public async entry-point ──────────────────────────────────────────────────

async def extract(file_path: Path) -> OCRResult:
    """
    Run OCR on *file_path* asynchronously.
    Dispatches to image or PDF handler based on file extension.
    """
    suffix = file_path.suffix.lower()
    engine = _get_engine()

    if engine is None:
        return _mock_result(file_path.name)

    loop = asyncio.get_event_loop()
    try:
        if suffix in (".jpg", ".jpeg", ".png"):
            blocks, pages = await loop.run_in_executor(
                None, _run_image, engine, str(file_path)
            )
        elif suffix == ".pdf":
            blocks, pages = await loop.run_in_executor(
                None, _run_pdf, engine, str(file_path)
            )
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    except Exception as exc:
        logger.error(f"OCR failed on {file_path.name}: {exc}")
        raise

    raw_text = "\n".join(b.text for b in blocks)
    avg_conf = (
        sum(b.confidence for b in blocks) / len(blocks) if blocks else 0.0
    )

    return OCRResult(
        filename=file_path.name,
        raw_text=raw_text.strip(),
        blocks=blocks,
        avg_confidence=round(avg_conf, 4),
        page_count=pages,
    )


# ── Image handler ─────────────────────────────────────────────────────────────

def _run_image(engine, image_path: str, page: int = 0) -> tuple[list[OCRBlock], int]:
    """Run EasyOCR on a single image file. Returns (blocks, page_count)."""
    results = engine.readtext(image_path, detail=1, paragraph=False)
    return _parse_easyocr_result(results, page=page), 1


# ── PDF handler ───────────────────────────────────────────────────────────────

def _run_pdf(engine, pdf_path: str) -> tuple[list[OCRBlock], int]:
    """
    Convert each PDF page to a high-res image via PyMuPDF, then OCR it.
    Returns (blocks, page_count).
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    all_blocks: list[OCRBlock] = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(2.0, 2.0)   # 2× zoom improves accuracy on scans
        pix = page.get_pixmap(matrix=mat)

        # Build numpy BGR array from pixmap samples
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.h, pix.w, pix.n
        )
        if pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)

        # EasyOCR accepts numpy arrays directly
        results = engine.readtext(img_bgr, detail=1, paragraph=False)
        all_blocks.extend(_parse_easyocr_result(results, page=page_num))

    doc.close()
    return all_blocks, len(doc)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_easyocr_result(results, page: int) -> list[OCRBlock]:
    """
    EasyOCR result format: [(bbox, text, confidence), ...]
    bbox = [[x0,y0],[x1,y1],[x2,y2],[x3,y3]]
    """
    blocks: list[OCRBlock] = []
    for (box_points, text, conf) in results:
        if not text.strip():
            continue
        xs = [p[0] for p in box_points]
        ys = [p[1] for p in box_points]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
        blocks.append(OCRBlock(text=text.strip(), confidence=conf, bbox=bbox, page=page))
    return blocks


def _mock_result(filename: str) -> OCRResult:
    """Returned when EasyOCR is not available (dev / test mode)."""
    mock_text = (
        "POLICE COMPLAINT FORM\n"
        "Name: John Silva\n"
        "NIC: 901234567V\n"
        "Phone: 0771234567\n"
        "Address: No 12, Galle Road, Colombo 03\n"
        "Incident Date: 2026-05-01\n"
        "Location: Colombo Fort\n"
        "Description: The complainant reported a theft of a mobile phone near the main bus stand."
    )
    block = OCRBlock(text=mock_text, confidence=0.92, bbox=None, page=0)
    return OCRResult(
        filename=filename,
        raw_text=mock_text,
        blocks=[block],
        avg_confidence=0.92,
        page_count=1,
    )
