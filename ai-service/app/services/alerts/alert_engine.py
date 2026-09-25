import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ── Alert Definitions ────────────────────────────────────────────────────────

class AlertSeverity:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    INFO = "INFO"

class AlertType:
    CRITICAL_RISK = "CRITICAL RISK"
    PATTERN = "PATTERN DETECTED"
    PRIORITY = "HIGH PRIORITY"

# ── Logic Thresholds ─────────────────────────────────────────────────────────
CRITICAL_SCORE_THRESHOLD = 0.75
PATTERN_COUNT_THRESHOLD = 3
WEAPON_KEYWORDS = {"gun", "knife", "bomb", "weapon", "pistol", "sword", "explosive", "shotgun"}

def generate_alerts(category: str, risk_score: float, keywords: List[str], location_history: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate actionable alerts based on AI model outputs and incident context.
    """
    alerts = []
    
    # 1. High Risk Logic -> CRITICAL RISK
    if risk_score >= CRITICAL_SCORE_THRESHOLD:
        alerts.append({
            "alertType": AlertType.CRITICAL_RISK,
            "message": f"High-risk {category} incident. This case requires immediate intervention.",
            "severity": AlertSeverity.CRITICAL
        })
        
    # 2. Repeated Complaints Logic -> PATTERN DETECTED
    # Assuming location_history contains 'previous_count' or similar
    prev_count = location_history.get("previous_count", 0)
    if prev_count >= PATTERN_COUNT_THRESHOLD:
        alerts.append({
            "alertType": AlertType.PATTERN,
            "message": f"Criminal pattern detected at this location ({prev_count} incidents in 30 days).",
            "severity": AlertSeverity.HIGH
        })
        
    # 3. Weapon Keywords Logic -> HIGH PRIORITY
    found_weapons = [kw for kw in keywords if kw.lower() in WEAPON_KEYWORDS]
    if found_weapons:
        alerts.append({
            "alertType": AlertType.PRIORITY,
            "message": f"High priority: Weapon-related keywords detected ({', '.join(found_weapons)}).",
            "severity": AlertSeverity.HIGH
        })
        
    # Log generation for debugging
    if alerts:
        logger.info(f"Generated {len(alerts)} alerts for category: {category}")
        
    return alerts
