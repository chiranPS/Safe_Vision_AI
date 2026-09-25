import re
import logging
import os
import joblib
from typing import Optional

from ...models.pipeline_models import OCRResult, KIEResult, MLResult

logger = logging.getLogger(__name__)

# ── Inference Service ────────────────────────────────────────────────────────

def predict_category(description: str) -> str:
    """
    Standalone fast inference: string description -> predicted category name.
    Optimized for high-speed single-document classification.
    """
    if not description or not description.strip():
        return "General"
        
    model, vectorizer = _load_assets()
    if not model or not vectorizer:
        # Fallback to rule-based detection if model isn't trained yet
        cat, _, _ = _detect_category(description.lower())
        return cat

    try:
        X = vectorizer.transform([description.lower()])
        return str(model.predict(X)[0])
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return "General"

# ── Assets Loading ───────────────────────────────────────────────────────────
_model = None
_vectorizer = None

def _load_assets():
    global _model, _vectorizer
    if _model is None or _vectorizer is None:
        try:
            base_path = os.path.dirname(__file__)
            model_path = os.path.join(base_path, "assets", "classifier_model.joblib")
            vec_path = os.path.join(base_path, "assets", "vectorizer.joblib")
            
            if os.path.exists(model_path) and os.path.exists(vec_path):
                _model = joblib.load(model_path)
                _vectorizer = joblib.load(vec_path)
                logger.info("ML Classifier assets loaded successfully.")
            else:
                logger.warning("ML assets not found. Falling back to rule-based classification.")
        except Exception as e:
            logger.error(f"Error loading ML assets: {e}")
    return _model, _vectorizer

# ── Category keyword map (Legacy/Fallback) ───────────────────────────────────
_CATEGORY_RULES: dict[str, list[str]] = {
    "Theft":        ["theft", "stolen", "stole", "rob", "robbed", "robbery", "pickpocket", "snatch"],
    "Assault":      ["assault", "attack", "beat", "hit", "punch", "kick", "slap", "violence", "injured"],
    "Narcotics":    ["drug", "narcotic", "heroin", "cocaine", "ice", "cannabis", "marijuana", "trafficking"],
    "Traffic":      ["accident", "collision", "crash", "vehicle", "motor", "road", "speeding", "drunk driving"],
    "Cybercrime":   ["cyber", "hack", "phish", "online", "internet", "social media", "password", "data breach"],
    "Homicide":     ["murder", "kill", "dead body", "death", "homicide", "manslaughter"],
    "Missing":      ["missing", "disappeared", "lost", "cannot find", "untraced"],
    "Harassment":   ["harass", "threaten", "intimidate", "stalk", "abuse", "molest"],
    "Domestic Violence": ["domestic", "spouse", "husband", "wife", "abuse", "beating", "screaming"],
}

# ── Priority rules ────────────────────────────────────────────────────────────
_CRITICAL_CATEGORIES  = {"Homicide", "Assault", "Domestic Violence"}
_HIGH_CATEGORIES      = {"Narcotics", "Fraud", "Missing", "Harassment"}
_MEDIUM_CATEGORIES    = {"Theft", "Traffic", "Cybercrime"}

_CRITICAL_KEYWORDS = ["murder", "kill", "dead", "hostage", "weapon", "gun", "knife", "bomb", "strangle"]
_HIGH_KEYWORDS     = ["missing child", "gang", "repeated", "organised", "systematic"]


# ── Public entry-point ────────────────────────────────────────────────────────

def classify(ocr: OCRResult, kie: KIEResult) -> MLResult:
    """
    Classify the complaint category and estimate priority.
    Uses a trained ML model if available, falling back to rule-based detection.
    """
    text = (ocr.raw_text + " " + (kie.description or "")).strip()
    
    # ── Try ML Prediction ────────────────────────────────────────────────────
    model, vectorizer = _load_assets()
    ml_category, ml_conf = None, 0.0
    
    if model and vectorizer and text:
        try:
            X = vectorizer.transform([text.lower()])
            ml_category = model.predict(X)[0]
            # Use predict_proba for confidence if supported
            if hasattr(model, "predict_proba"):
                ml_conf = float(max(model.predict_proba(X)[0]))
            else:
                ml_conf = 0.85 # Default if proba not available
            
            logger.info(f"ML Prediction: {ml_category} ({ml_conf:.2f})")
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")

    # ── Try Rule-based analysis (Fallback / Verification) ────────────────────
    rule_category, rule_score, keywords = _detect_category(text.lower())
    
    # ── Preference Logic ─────────────────────────────────────────────────────
    # 1. Highest priority: Explicit KIE-extracted category from checkboxes
    if kie.complaint_category:
        # If multiple, take the first one for classification
        final_category = kie.complaint_category.split(",")[0].strip()
        final_conf = 0.98
    # 2. Second priority: ML Prediction if high confidence
    elif ml_category and (ml_conf > 0.6 or rule_category == "General"):
        final_category = ml_category
        final_conf = ml_conf
    # 3. Third priority: Rule-based detection
    else:
        final_category = rule_category
        final_conf = rule_score

    priority, pri_score = _detect_priority(text.lower(), final_category)

    return MLResult(
        category=final_category,
        priority=priority,
        category_confidence=round(final_conf, 4),
        priority_confidence=round(pri_score, 4),
        keywords=keywords[:10],
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_category(text: str) -> tuple[str, float, list[str]]:
    """
    Score each category by counting keyword hits.
    Returns the top category, its normalised confidence, and hit keywords.
    """
    scores: dict[str, int] = {}
    hit_keywords: dict[str, list[str]] = {}

    for category, keywords in _CATEGORY_RULES.items():
        hits = [kw for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text)]
        scores[category] = len(hits)
        hit_keywords[category] = hits

    if not any(scores.values()):
        return "General", 0.5, []

    best = max(scores, key=scores.get)
    total_keywords = len(_CATEGORY_RULES[best])
    confidence = min(scores[best] / max(total_keywords, 1), 1.0)
    confidence = max(confidence, 0.6) if scores[best] > 0 else 0.5

    return best, confidence, hit_keywords[best]


def _detect_priority(text: str, category: str) -> tuple[str, float]:
    """
    Derive priority from category + critical/high keyword presence.
    """
    for kw in _CRITICAL_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            return "Critical", 0.95

    if category in _CRITICAL_CATEGORIES:
        return "Critical", 0.88

    for kw in _HIGH_KEYWORDS:
        if kw in text:
            return "High", 0.80

    if category in _HIGH_CATEGORIES:
        return "High", 0.78

    if category in _MEDIUM_CATEGORIES:
        return "Medium", 0.70

    return "Low", 0.60
