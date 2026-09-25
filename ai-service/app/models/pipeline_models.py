"""
Shared intermediate data structures that flow through the AI pipeline.
Each stage consumes and enriches these models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ─────────────────────────────────────────────
# Stage 1 Output: OCR Layer
# ─────────────────────────────────────────────

class OCRBlock(BaseModel):
    """A single detected text block (paragraph, heading, etc.)."""
    text: str
    confidence: float
    type: str = "text"              # "text" | "heading" | "table" | "list_item"
    bbox: Optional[List[float]] = None   # [x0, y0, x1, y1]
    page: int = 0


class OCRResult(BaseModel):
    """Full OCR result for an uploaded document."""
    filename: str
    raw_text: str
    blocks: List[OCRBlock] = []
    tables: List[Dict[str, Any]] = [] # For structured table data
    avg_confidence: float
    page_count: int = 1


# ─────────────────────────────────────────────
# Stage 2 Output: KIE Layer
# ─────────────────────────────────────────────

class ExtractedField(BaseModel):
    """A single extracted key-value field from the form."""
    key: str
    value: str
    confidence: float = 1.0
    source: str = "regex"   # "regex" | "heuristic" | "ml"


class KIEResult(BaseModel):
    """Key Information Extraction result."""
    fields: List[ExtractedField] = []
    
    # COMPLAINT INFORMATION
    reference_number: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    police_station: Optional[str] = None
    complaint_category: Optional[str] = None
    
    # COMPLAINANT DETAILS
    complainant_name: Optional[str] = None
    nic_number: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    employer_address: Optional[str] = None
    email: Optional[str] = None

    # INCIDENT DETAILS
    incident_date: Optional[str] = None
    incident_time: Optional[str] = None
    location: Optional[str] = None
    persons_involved: Optional[str] = None
    suspected_individuals: Optional[str] = None
    vehicle_details: Optional[str] = None

    # DESCRIPTION
    description: Optional[str] = None

    # EVIDENCE & CATEGORY FLAGS (Checkboxes)
    has_photos: bool = False
    has_medical_report: bool = False
    has_cctv: bool = False
    has_witness_statement: bool = False
    has_audio_recording: bool = False
    has_other_evidence: bool = False
    evidence_notes: Optional[str] = None
    
    # Category Checkboxes
    is_theft: bool = False
    is_assault: bool = False
    is_narcotics: bool = False
    is_traffic: bool = False
    is_domestic_violence: bool = False
    is_child_abuse: bool = False
    is_suspicious_activity: bool = False
    is_other_category: bool = False

    # OFFICER USE ONLY
    receiving_officer_name: Optional[str] = None
    badge_number: Optional[str] = None
    rank: Optional[str] = None
    branch: Optional[str] = None
    assigned_station: Optional[str] = None
    signature_present: bool = False
    date_received: Optional[str] = None
    manual_notes: Optional[str] = None


# ─────────────────────────────────────────────
# Stage 3 Output: ML Layer
# ─────────────────────────────────────────────

class MLResult(BaseModel):
    """ML classification and prediction result."""
    category: str = "Unknown"
    priority: str = "Medium"          # Low | Medium | High | Critical
    category_confidence: float = 0.0
    priority_confidence: float = 0.0
    keywords: List[str] = []


# ─────────────────────────────────────────────
# Stage 4 Output: Alerts Layer
# ─────────────────────────────────────────────

class RiskAlert(BaseModel):
    """A single generated risk alert."""
    level: str       # "info" | "warning" | "critical"
    message: str
    rule: str        # The rule that triggered this alert


class AlertResult(BaseModel):
    """Risk assessment and alert output."""
    risk_score: float = 0.0           # 0.0 – 1.0
    is_hotspot: bool = False
    alerts: List[RiskAlert] = []


# ─────────────────────────────────────────────
# Final Pipeline Output
# ─────────────────────────────────────────────

class PipelineResult(BaseModel):
    """
    The complete structured output of the complaint processing pipeline.
    This is returned directly by the API and consumed by the Next.js backend.
    """
    filename: str
    raw_text: str
    ocr_confidence: float
    extracted_fields: KIEResult
    classification: MLResult
    risk_assessment: AlertResult
    metadata: Dict[str, Any] = Field(default_factory=dict)
