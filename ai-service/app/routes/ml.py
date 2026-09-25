from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.ml.classifier import predict_category
from app.services.ml.risk_predictor import predict_risk
from app.services.alerts.alert_engine import generate_alerts

router = APIRouter(prefix="/ml", tags=["ML Classification"])

class TextInferenceRequest(BaseModel):
    description: str

class TextInferenceResponse(BaseModel):
    category: str

class RiskInferenceRequest(BaseModel):
    category: str
    metadata: Dict[str, Any] = {}

class RiskInferenceResponse(BaseModel):
    riskScore: float
    urgencyLevel: str

class AlertGenerationRequest(BaseModel):
    category: str
    riskScore: float
    keywords: List[str] = []
    location_history: Dict[str, Any] = {}

class AlertInfo(BaseModel):
    alertType: str
    message: str
    severity: str

class AlertGenerationResponse(BaseModel):
    alerts: List[AlertInfo]

@router.post("/classify", response_model=TextInferenceResponse)
async def classify_text(request: TextInferenceRequest = Body(...)):
    """
    Direct text-to-category classification.
    Takes a complaint description string and returns the predicted category.
    """
    category = predict_category(request.description)
    return TextInferenceResponse(category=category)

@router.post("/risk", response_model=RiskInferenceResponse)
async def predict_complaint_risk(request: RiskInferenceRequest = Body(...)):
    """
    Predict the risk score and urgency level for a given category and metadata.
    Metadata can include 'hour' (0-23) and 'location_frequency'.
    """
    score, urgency = predict_risk(request.category, request.metadata)
    return RiskInferenceResponse(riskScore=score, urgencyLevel=urgency)

@router.post("/alerts", response_model=AlertGenerationResponse)
async def get_alerts(request: AlertGenerationRequest = Body(...)):
    """
    Generate security alerts based on risk, keywords, and history.
    """
    alerts = generate_alerts(
        request.category, 
        request.riskScore, 
        request.keywords, 
        request.location_history
    )
    return AlertGenerationResponse(alerts=alerts)
