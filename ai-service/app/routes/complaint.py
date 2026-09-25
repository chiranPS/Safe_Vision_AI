"""
Complaint processing route.
POST /complaint/process  — accepts a document upload, runs the full pipeline,
                           and returns a structured PipelineResult JSON.
"""
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.pipeline_models import PipelineResult
from app.services.pipeline import process_complaint_pipeline
from app.utils.file_handler import save_upload_file

router = APIRouter(prefix="/complaint", tags=["Complaint Pipeline"])

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


@router.post("/process")
async def process_complaint(file: UploadFile = File(...)):
    """
    Upload a scanned police complaint form (JPG / PNG / PDF).

    The document is passed through a five-stage AI pipeline:
    - **OCR**          — extracts raw text via PaddleOCR/Docling
    - **KIE**          — detects structured fields (name, NIC, phone, location …)
    - **Classification** — ML-driven category prediction
    - **Risk**         — ML-driven risk scoring (RandomForest)
    - **Alerts**       — AI-generated security alerts

    Returns a structured JSON with complainant, complaint, and risk data.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}",
        )

    saved_path: Path | None = None
    try:
        saved_path = await save_upload_file(file)
        result = await process_complaint_pipeline(saved_path)
        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(exc)}")
    finally:
        if saved_path and saved_path.exists():
            try:
                saved_path.unlink()
            except Exception as exc:
                print(f"[Cleanup] Failed to delete temp file {saved_path}: {exc}")
