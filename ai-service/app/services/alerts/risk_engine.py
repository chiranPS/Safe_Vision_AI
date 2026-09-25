"""
Alerts Stage — Rule-based risk scoring and alert generation.
Consumes ML classification results + OCR text to produce a risk score
and a list of actionable RiskAlerts.  Works 100% offline.
Outputs AlertResult.
"""
import logging

import os
import joblib
import pandas as pd
from datetime import datetime
from ...models.pipeline_models import MLResult, KIEResult, RiskAlert, AlertResult

logger = logging.getLogger(__name__)

# ── Model Loading ────────────────────────────────────────────────────────────
_risk_model = None

def _load_risk_model():
    global _risk_model
    if _risk_model is None:
        try:
            model_path = os.path.join(os.path.dirname(__file__), "..", "ml", "assets", "risk_model.joblib")
            if os.path.exists(model_path):
                _risk_model = joblib.load(model_path)
                logger.info("ML Risk model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load risk model: {e}")
    return _risk_model

# ── Legacy weights (Fallback) ─────────────────────────────────────────────────
_PRIORITY_SCORES = {
    "Critical": 0.90,
    "High":     0.65,
    "Medium":   0.40,
    "Low":      0.15,
}

_CATEGORY_MULTIPLIERS = {
    "Homicide":   1.20,
    "Assault":    1.10,
    "Narcotics":  1.05,
    "Missing":    1.05,
    "Fraud":      0.95,
    "Theft":      0.90,
    "Traffic":    0.85,
    "Cybercrime": 0.85,
    "Harassment": 1.00,
    "General":    0.80,
}

# Hotspot threshold
_HOTSPOT_THRESHOLD = 0.60


# ── Public entry-point ────────────────────────────────────────────────────────

def assess(ml: MLResult, kie: KIEResult) -> AlertResult:
    """
    Generate a risk score and list of alerts based on ML + KIE outputs.
    Uses RandomForest ML model if available.
    """
    alerts: list[RiskAlert] = []
    risk_score = 0.0

    # ── Try ML-based Risk Scoring ────────────────────────────────────────────
    model = _load_risk_model()
    if model:
        try:
            # Extract features
            hour = 12 # Default
            if kie.incident_date:
                # Try to extract hour if available in string (heuristic)
                try:
                    # Very simple extraction for now
                    if ":" in kie.incident_date:
                        hour = int(kie.incident_date.split(":")[0][-2:])
                except: pass
            
            # For location frequency, we'd normally query a DB. 
            # Mocking it as 5 for now or extracting from metadata if we had it.
            loc_freq = 5 
            
            input_df = pd.DataFrame([{
                "category": ml.category,
                "hour": hour,
                "location_frequency": loc_freq
            }])
            
            risk_score = float(model.predict(input_df)[0])
            logger.info(f"ML Risk Score: {risk_score:.4f}")
            
        except Exception as e:
            logger.error(f"ML Risk assessment failed: {e}")
            model = None # Trigger fallback

    # ── Fallback to Rule-based Scoring ───────────────────────────────────────
    if not model or risk_score == 0.0:
        base_score = _PRIORITY_SCORES.get(ml.priority, 0.40)
        multiplier = _CATEGORY_MULTIPLIERS.get(ml.category, 1.0)
        risk_score = min(base_score * multiplier, 1.0)

    # ── Rule-based alert generation ───────────────────────────────────────────

    if ml.priority == "Critical":
        alerts.append(RiskAlert(
            level="critical",
            message=f"Critical-priority {ml.category} complaint detected. Immediate escalation required.",
            rule="priority_critical",
        ))

    if ml.priority == "High":
        alerts.append(RiskAlert(
            level="warning",
            message=f"High-priority {ml.category} case. Assign a Lead Officer within 2 hours.",
            rule="priority_high",
        ))

    if ml.category == "Homicide":
        alerts.append(RiskAlert(
            level="critical",
            message="Homicide keywords detected. CID notification may be required.",
            rule="category_homicide",
        ))

    if ml.category == "Narcotics":
        alerts.append(RiskAlert(
            level="warning",
            message="Narcotics-related complaint. Route to Narcotics Bureau.",
            rule="category_narcotics",
        ))

    if ml.category == "Missing":
        alerts.append(RiskAlert(
            level="warning",
            message="Missing person report. Time-sensitive — escalate within 1 hour.",
            rule="category_missing",
        ))

    # Check if complainant contact details are incomplete
    if not kie.nic_number:
        alerts.append(RiskAlert(
            level="info",
            message="Complainant NIC not detected in document. Manual verification required.",
            rule="missing_nic",
        ))

    if not kie.phone:
        alerts.append(RiskAlert(
            level="info",
            message="Complainant phone number not detected. Follow-up contact may be difficult.",
            rule="missing_phone",
        ))

    # Low confidence OCR warning is handled upstream — no duplicate here

    is_hotspot = risk_score >= _HOTSPOT_THRESHOLD

    if is_hotspot:
        alerts.append(RiskAlert(
            level="warning",
            message=f"Risk score {risk_score:.2f} exceeds hotspot threshold. Location flagged for patrol.",
            rule="hotspot_threshold",
        ))

    logger.debug(
        f"Risk assessment: score={risk_score:.2f}, hotspot={is_hotspot}, alerts={len(alerts)}"
    )

    return AlertResult(
        risk_score=round(risk_score, 4),
        is_hotspot=is_hotspot,
        alerts=alerts,
    )
