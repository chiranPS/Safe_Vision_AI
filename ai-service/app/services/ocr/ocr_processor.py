"""
OCR Orchestrator — Combines PaddleOCR and Docling.
"""
import asyncio
import logging
from pathlib import Path

from .paddle_handler import extract_text as run_paddle
from .docling_handler import parse_pdf as run_docling
from ...models.pipeline_models import OCRResult

logger = logging.getLogger(__name__)

async def extract(file_path: Path) -> OCRResult:
    """
    Orchestrate OCR and layout analysis.
    For PDFs: Run Docling for structure + PaddleOCR for text refinement.
    For Images: Run PaddleOCR.
    """
    suffix = file_path.suffix.lower()
    filename = file_path.name
    
    loop = asyncio.get_event_loop()
    
    if suffix == '.pdf':
        logger.info(f"Running dual pipeline (Docling + PaddleOCR) for {filename}")
        
        # Run sequentially to save memory
        logger.info(f"Starting Docling stage for {filename}...")
        docling_res = await loop.run_in_executor(None, run_docling, file_path)
        
        logger.info(f"Starting PaddleOCR stage for {filename}...")
        paddle_res = await loop.run_in_executor(None, run_paddle, file_path)
        
        blocks, tables, docling_text = docling_res
        paddle_blocks, page_count = paddle_res
        
        # Combine: Use Docling for structured blocks (headings, tables) 
        # and PaddleOCR for raw text content if Docling text is sparse
        raw_text = docling_text if len(docling_text) > len("\n".join([b.text for b in paddle_blocks])) else "\n".join([b.text for b in paddle_blocks])
        
        # Calculate average confidence from PaddleOCR
        avg_conf = sum(b.confidence for b in paddle_blocks) / len(paddle_blocks) if paddle_blocks else 0.9
        
        return OCRResult(
            filename=filename,
            raw_text=raw_text,
            blocks=blocks or paddle_blocks, # Prefer Docling blocks for structure
            tables=tables,
            avg_confidence=round(avg_conf, 4),
            page_count=max(page_count, 1)
        )
    
    else:
        # Image pipeline
        logger.info(f"Running PaddleOCR pipeline for image {filename}")
        paddle_blocks, page_count = await loop.run_in_executor(None, run_paddle, file_path)
        
        raw_text = "\n".join([b.text for b in paddle_blocks])
        avg_conf = sum(b.confidence for b in paddle_blocks) / len(paddle_blocks) if paddle_blocks else 0.0
        
        return OCRResult(
            filename=filename,
            raw_text=raw_text,
            blocks=paddle_blocks,
            tables=[],
            avg_confidence=round(avg_conf, 4),
            page_count=page_count
        )
