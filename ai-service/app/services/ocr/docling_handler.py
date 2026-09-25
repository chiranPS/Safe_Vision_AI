"""
Docling Stage — Layout-aware PDF extraction.
Detects headings, paragraphs, and tables while preserving coordinates.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from ...models.pipeline_models import OCRBlock, OCRResult

logger = logging.getLogger(__name__)

# Lazy-load Docling components
_converter = None

def _get_converter():
    global _converter
    if _converter is None:
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
            
            # Optimization: Disable internal OCR and Table Structure as we use PaddleOCR for text
            # and to minimize memory footprint on machines with small paging files.
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False 
            pipeline_options.do_table_structure = False 
            
            # Limit threads to reduce memory pressure
            pipeline_options.accelerator_options = AcceleratorOptions(num_threads=2)
            
            _converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            logger.info("Docling DocumentConverter initialised successfully (Optimised).")
        except Exception as exc:
            logger.warning(f"Docling unavailable: {exc}")
    return _converter

def parse_pdf(file_path: Path) -> Tuple[List[OCRBlock], List[Dict[str, Any]], str]:
    """
    Parse a PDF using Docling to extract structured blocks and tables.
    Returns (blocks, tables, raw_text).
    """
    converter = _get_converter()
    if not converter:
        return [], [], ""

    try:
        result = converter.convert(file_path)
        doc = result.document
        
        blocks = []
        tables = []
        raw_text_parts = []

        # Iterate through document elements
        for element in doc.texts:
            # element.label can be "paragraph", "heading", etc.
            text = element.text
            raw_text_parts.append(text)
            
            bbox = None
            if hasattr(element, "prov") and element.prov:
                # Element coordinates if available
                # Docling prov often contains page and bbox
                prov = element.prov[0]
                if hasattr(prov, "bbox"):
                    b = prov.bbox
                    # Normalize coordinates [x0, y0, x1, y1]
                    bbox = [float(b.l), float(b.t), float(b.r), float(b.b)]
            
            blocks.append(OCRBlock(
                text=text,
                confidence=1.0, # Docling doesn't always provide confidence per text block easily
                type=element.label or "text",
                bbox=bbox,
                page=(element.prov[0].page_no - 1) if hasattr(element, "prov") and element.prov else 0
            ))

        # Extract tables
        for table in doc.tables:
            # Simple conversion of table to dict representation
            # You can customize this based on how the frontend needs it
            tables.append({
                "label": table.label,
                "data": table.export_to_dataframe().to_dict(orient="records") if hasattr(table, "export_to_dataframe") else []
            })

        return blocks, tables, "\n".join(raw_text_parts)

    except Exception as exc:
        logger.error(f"Docling PDF parsing failed: {exc}")
        return [], [], ""
