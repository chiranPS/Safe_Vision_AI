from pydantic import BaseModel

class OCRResponse(BaseModel):
    rawText: str
    confidenceScore: float
