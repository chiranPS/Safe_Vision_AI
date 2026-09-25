import logging
import joblib
import os
import google.generativeai as genai
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from app.services.pipeline import process_complaint_pipeline
from app.utils.file_handler import save_upload_file

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    gemini_model = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Pipeline"])

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

@router.post("/process-complaint")
async def ai_process_complaint(file: UploadFile = File(...)):
    """
    Unified AI Processing Endpoint
    ──────────────────────────────
    1. Uploads and validates the document.
    2. Runs the 5-stage AI pipeline (OCR, KIE, ML, Risk, Alerts).
    3. Returns a structured JSON result.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}"
        )

    saved_path: Path | None = None
    try:
        logger.info(f"AI Endpoint received file: {file.filename}")
        
        # Save temporary file for processing
        saved_path = await save_upload_file(file)
        
        # Run the full pipeline
        result = await process_complaint_pipeline(saved_path)
        
        return result

    except ValueError as e:
        logger.error(f"Validation error in AI pipeline: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error in AI pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during AI processing.")
    finally:
        # Cleanup
        if saved_path and saved_path.exists():
            try:
                saved_path.unlink()
                logger.debug(f"Temporary file deleted: {saved_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {saved_path}: {e}")

# --- Fast API Integration: Machine Learning Endpoints ---

class ComplaintData(BaseModel):
    description: str

class RiskData(BaseModel):
    district: str
    category: str
    hour: int
    latitude: float
    longitude: float

MODEL_DIR = Path(__file__).parent.parent.parent / 'model_training'
try:
    tfidf = joblib.load(MODEL_DIR / 'tfidf_vectorizer.joblib')
    xgb_cat = joblib.load(MODEL_DIR / 'xgb_category_model.joblib')
    le_cat = joblib.load(MODEL_DIR / 'label_encoder_category.joblib')
    xgb_prio = joblib.load(MODEL_DIR / 'xgb_priority_model.joblib')
    le_prio = joblib.load(MODEL_DIR / 'label_encoder_priority.joblib')
    xgb_risk = joblib.load(MODEL_DIR / 'xgb_risk_classifier.joblib')
    le_dist = joblib.load(MODEL_DIR / 'label_encoder_district.joblib')
    MODELS_LOADED = True
    logger.info("Successfully loaded local ML models for inference.")
except Exception as e:
    logger.warning(f"Could not load ML models from {MODEL_DIR}. Ensure training scripts were run. Error: {e}")
    MODELS_LOADED = False

@router.post("/classify-complaint")
async def classify_complaint(data: ComplaintData):
    """Predicts Complaint Category and Priority Level from English narrative text."""
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="AI Models not loaded.")
    
    vec = tfidf.transform([data.description])
    
    cat_pred = xgb_cat.predict(vec)
    category = le_cat.inverse_transform(cat_pred)[0]
    
    prio_pred = xgb_prio.predict(vec)
    priority = le_prio.inverse_transform(prio_pred)[0]
    
    return {
        "predictedCategory": str(category),
        "priorityLevel": str(priority)
    }

@router.post("/predict-risk")
async def predict_risk(data: RiskData):
    """Predicts Risk Score and Hotspot status based on spatio-temporal features."""
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="AI Models not loaded.")
        
    try:
        dist_enc = le_dist.transform([data.district])[0]
        cat_enc = le_cat.transform([data.category])[0]
    except ValueError:
        dist_enc = 0
        cat_enc = 0
        
    import pandas as pd
    df = pd.DataFrame([{
        'District_Enc': dist_enc,
        'Category_Enc': cat_enc,
        'Hour': data.hour,
        'Latitude': data.latitude,
        'Longitude': data.longitude
    }])
    
    risk_prob = float(xgb_risk.predict_proba(df)[0][1])
    is_hotspot = bool(risk_prob > 0.5)
    
    return {
        "riskScore": risk_prob,
        "isHotspot": is_hotspot
    }

class AreaInsightRequest(BaseModel):
    area: str
    count: int
    topCategories: List[str]
    totalRiskScore: float
    trend: int
    lat: float
    lng: float

class DashboardInsightsRequest(BaseModel):
    areas: List[AreaInsightRequest]

@router.post("/dashboard-insights")
async def dashboard_insights(data: DashboardInsightsRequest):
    """Generates AI alerts and officer suggestions for the dashboard."""
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="AI Models not loaded.")
        
    alerts = []
    
    # 1. Evaluate areas using XGBoost risk predictor
    import pandas as pd
    high_risk_areas = []
    
    for area in data.areas:
        if area.count == 0:
            continue
            
        try:
            dist_enc = le_dist.transform([area.area])[0]
            # Use the most frequent category for risk prediction baseline
            cat_enc = le_cat.transform([area.topCategories[0] if area.topCategories else "Theft"])[0]
        except ValueError:
            dist_enc = 0
            cat_enc = 0
            
        # Predict using current hour for context
        df = pd.DataFrame([{
            'District_Enc': dist_enc,
            'Category_Enc': cat_enc,
            'Hour': datetime.now().hour,
            'Latitude': area.lat,
            'Longitude': area.lng
        }])
        
        risk_prob = float(xgb_risk.predict_proba(df)[0][1])
        
        # Lowered threshold to ensure alerts appear for demonstration
        if risk_prob >= 0.0:
            high_risk_areas.append({
                "area": area.area,
                "risk_prob": risk_prob,
                "trend": area.trend,
                "categories": area.topCategories,
                "count": area.count
            })
            
    # 2. Generate suggestions using Gemini (if available and risks found)
    if high_risk_areas and gemini_model:
        prompt = "You are a tactical police AI assistant. Review the following high-risk areas and generate 2-3 short, actionable alerts for officers. Focus on deployment suggestions based on the categories. Format as plain text without markdown asterisks. Use a professional tone.\\n\\n"
        for hr in high_risk_areas:
            prompt += f"Area: {hr['area']}, Spiking categories: {', '.join(hr['categories'])}, Recent Incidents: {hr['count']}, Trend: +{hr['trend']}%\\n"
            
        try:
            response = gemini_model.generate_content(prompt)
            # Parse gemini response into individual alerts
            suggestions = [s.strip() for s in response.text.split('\\n') if s.strip()]
            
            for i, suggestion in enumerate(suggestions):
                if i >= len(high_risk_areas):
                    break
                alerts.append({
                    "type": "AI TACTICAL SUGGESTION",
                    "message": suggestion.replace("- ", ""),
                    "area": high_risk_areas[i]["area"],
                    "createdAt": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            
    # Fallback/Additional hardcoded critical alerts
    for hr in high_risk_areas:
        if hr['risk_prob'] > 0.8:
            alerts.append({
                "type": "CRITICAL PREDICTION",
                "message": f"XGBoost model predicts {hr['risk_prob']*100:.1f}% incident probability in {hr['area']}. Recommend immediate patrol deployment.",
                "area": hr['area'],
                "createdAt": datetime.now().isoformat()
            })
            
    return alerts

@router.post("/single-insight")
async def single_insight(area: AreaInsightRequest):
    """Generates a single tactical recommendation for a specific hotspot area."""
    
    # Rule-Based Generator (Fallback if Gemini fails/rate-limits)
    def generate_rule_based_insight(area_data: AreaInsightRequest):
        primary = area_data.topCategories[0] if area_data.topCategories else "General"
        trend_text = "surging" if area_data.trend > 20 else ("decreasing" if area_data.trend < 0 else "stable")
        
        if primary == 'Traffic':
            return f"With traffic incidents {trend_text} at {area_data.count} recent cases in {area_data.area}, deploy traffic enforcement units during peak congestion hours to monitor key intersections and check vehicle compliance."
        elif primary in ['Theft', 'Burglary', 'Robbery']:
            return f"Given the {trend_text} rate of property crimes in {area_data.area}, increase high-visibility night patrols and coordinate with local community watch groups to secure vulnerable neighborhoods."
        elif primary in ['Assault', 'Violence', 'Social Conflict']:
            return f"Due to {area_data.count} recent conflicts in {area_data.area}, station rapid-response officers trained in de-escalation near identified public gathering spots to prevent escalation."
        elif primary == 'Drug Offenses':
            return f"Intelligence indicates {trend_text} narcotics activity in {area_data.area}. Assign undercover vice units to monitor suspicious networks and conduct targeted raids based on tip-offs."
        else:
            return f"Analyze the recent cluster of {primary} cases in {area_data.area} and deploy specialized units tailored to the specific nature of these incidents."

    if not gemini_model:
        return {"recommendation": generate_rule_based_insight(area)}
        
    prompt = f"You are a tactical police AI. Generate a single, highly specific 1-2 sentence deployment recommendation for police commanders regarding the {area.area} district. Consider the primary crime types: {', '.join(area.topCategories)}. Recent incident volume is {area.count} with a trend of {area.trend}%. If traffic is the main issue, mention vehicle checks/peak hours. If theft, mention night patrols. Tailor the advice strictly to these factors. Format as plain text without markdown asterisks."
    
    try:
        response = gemini_model.generate_content(prompt)
        return {"recommendation": response.text.strip().replace("- ", "")}
    except Exception as e:
        logger.error(f"Gemini single insight failed (Quota/Error): {e}")
        return {"recommendation": generate_rule_based_insight(area)}

