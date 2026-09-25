"""
Safe-Vision AI Service — FastAPI application entry point.
"""
import logging
import os

# Disable PIR and oneDNN to prevent crashes on Windows with PaddlePaddle 3.x
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_enable_new_executor'] = '0'
os.environ['PADDLE_PIR_ENABLE'] = '0'
os.environ['PADDLE_PIR_MODE'] = '0'

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import ocr, complaint, ml, ai

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

app = FastAPI(
    title="Safe-Vision AI Service",
    description=(
        "Modular AI microservice for the Safe-Vision police complaint system.\n\n"
        "**Pipeline stages:** OCR → KIE → ML Classification → Risk Alerts"
    ),
    version="2.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Restrict origins in production via ALLOWED_ORIGINS env var
_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ocr.router)           # legacy: POST /ocr/process
app.include_router(complaint.router)     # new:    POST /complaint/process
app.include_router(ml.router)            # utility: POST /ml/classify
app.include_router(ai.router)            # unified: POST /ai/process-complaint


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Verify the service is running and return version info."""
    return {
        "status": "healthy",
        "service": "Safe-Vision AI Service",
        "version": "2.0.0",
        "pipeline_stages": ["OCR", "KIE", "ML", "Alerts"],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
