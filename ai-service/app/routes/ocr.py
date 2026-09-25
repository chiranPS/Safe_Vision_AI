from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.ocr_models import OCRResponse
from app.utils.file_handler import save_upload_file
from app.services.ocr_service import process_document

router = APIRouter(
    prefix="/ocr",
    tags=["OCR Processing"]
)

@router.post("/process", response_model=OCRResponse)
async def process_ocr(file: UploadFile = File(...)):
    """
    Upload a document (image/pdf) to be processed by the AI service.
    Returns extracted text, summary, and entities.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    try:
        # Validate file type
        valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in valid_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(valid_extensions)}")

        # Save file temporarily
        saved_path = await save_upload_file(file)
        
        # Process the file using the AI service
        response = await process_document(saved_path, file.filename)
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Cleanup temporary file
        if 'saved_path' in locals() and saved_path.exists():
            try:
                saved_path.unlink()
            except Exception as e:
                print(f"Failed to delete temp file {saved_path}: {e}")
