"""Map OCR token predictions to police form fields."""

from __future__ import annotations

from typing import Any

FIELD_LABELS = {
    0: "other",
    1: "date",
    2: "complainant_name",
    3: "case_description",
    4: "location",
    5: "officer_name",
    6: "complaint_reference_number",
    7: "badge_number",
}

LABEL_TO_FIELD = {
    "date": "date",
    "complainant_name": "complainant_name",
    "case_description": "case_description",
    "location": "location",
    "officer_name": "officer_name",
    "complaint_reference_number": "complaint_reference_number",
    "badge_number": "badge_number",
}


def map_tokens_to_fields(tokens: list[dict], raw_text: str) -> dict[str, Any]:
    """Aggregate token predictions into form fields."""
    fields: dict[str, dict] = {}

    for token in tokens:
        label = token.get("label") or FIELD_LABELS.get(token.get("label_id", 0), "other")
        if label == "other":
            continue
        field_name = LABEL_TO_FIELD.get(label, label)
        entry = fields.setdefault(
            field_name, {"value": "", "confidence": 0.0, "low_confidence": False}
        )
        entry["value"] = (entry["value"] + " " + token["text"]).strip()
        entry["confidence"] = max(entry["confidence"], token.get("confidence", 0.5))
        entry["low_confidence"] = entry["confidence"] < 0.7

    if not fields and raw_text:
        fields["case_description"] = {
            "value": raw_text,
            "confidence": 0.5,
            "low_confidence": True,
        }

    return fields
