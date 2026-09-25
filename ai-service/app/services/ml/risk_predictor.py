import os
import joblib
import pandas as pd
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# ── Singleton Loading ────────────────────────────────────────────────────────
_risk_model = None

def _get_model():
    global _risk_model
    if _risk_model is None:
        try:
            # Locate assets relative to this file
            base_path = os.path.dirname(__file__)
            model_path = os.path.join(base_path, "assets", "risk_model.joblib")
            
            if os.path.exists(model_path):
                _risk_model = joblib.load(model_path)
                logger.info("Risk Prediction model loaded successfully.")
            else:
                logger.warning(f"Risk model asset not found at {model_path}")
        except Exception as e:
            logger.error(f"Error loading risk model: {e}")
    return _risk_model

def predict_risk(category: str, metadata: Dict[str, Any]) -> Tuple[float, str]:
    """
    Predict risk score and urgency level based on category and metadata.
    
    Metadata expected keys:
    - hour (int, 0-23)
    - location_frequency (int)
    """
    model = _get_model()
    
    # Extract features with defaults
    hour = metadata.get("hour", 12)
    loc_freq = metadata.get("location_frequency", 1)
    
    if model:
        try:
            input_df = pd.DataFrame([{
                "category": category,
                "hour": hour,
                "location_frequency": loc_freq
            }])
            
            score = float(model.predict(input_df)[0])
            score = max(0.0, min(1.0, score)) # Clamp between 0 and 1
            
            return score, _map_score_to_urgency(score)
            
        except Exception as e:
            logger.error(f"Risk prediction error: {e}")
    
    # Basic fallback if model fails
    return 0.5, "Medium"

def _map_score_to_urgency(score: float) -> str:
    if score >= 0.8: return "Critical"
    if score >= 0.6: return "High"
    if score >= 0.3: return "Medium"
    return "Low"
