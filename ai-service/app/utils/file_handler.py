import os
import shutil
from fastapi import UploadFile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

# Ensure upload directory exists
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

async def save_upload_file(upload_file: UploadFile, destination: Path = None) -> Path:
    """
    Saves an uploaded file to the specified destination.
    Returns the Path to the saved file.
    """
    if not destination:
        destination = Path(UPLOAD_DIR) / upload_file.filename

    # Ensure the parent directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

    return destination
