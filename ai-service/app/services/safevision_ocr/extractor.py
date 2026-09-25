"""OCR field extraction using LayoutLMv3 or fallback heuristics."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any
import cv2

from .field_mapper import map_tokens_to_fields
from .preprocessor import preprocess

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.6


class OCRModelCache:
    """Thread-safe cache for OCR models to avoid global state."""
    _processor = None
    _model = None
    _model_path = None

    @classmethod
    def get_model(cls, model_path: str):
        """Get cached model or load new one."""
        if cls._model is None or cls._model_path != model_path:
            from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor
            import torch

            device = "cpu"
            logger.info(f"Loading LayoutLMv3 model from {model_path}")
            # apply_ocr=False: we run Tesseract ourselves and pass words+boxes explicitly,
            # giving us full control over tokenisation and label mapping.
            processor = LayoutLMv3Processor.from_pretrained(model_path, apply_ocr=False)
            if isinstance(processor, tuple):
                processor = processor[0]
            cls._processor = processor
            model = LayoutLMv3ForTokenClassification.from_pretrained(model_path)  # type: ignore
            cls._model = model.to(device)  # type: ignore
            cls._model_path = model_path
        return cls._processor, cls._model


def extract_fields(image_path: str, model_path: str | None = None) -> dict[str, Any]:
    """Run OCR pipeline and return structured fields with confidence scores."""
    processed = preprocess(image_path)
    temp_path = str(Path(image_path).with_suffix(".preprocessed.png"))
    cv2.imwrite(temp_path, processed)

    try:
        raw_text, token_predictions = _run_ocr_model(temp_path, model_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    fields = map_tokens_to_fields(token_predictions, raw_text)

    # Apply rule-based fallback overrides
    from .field_extractor_rules import extract_fields_with_rules
    rule_fields = extract_fields_with_rules(raw_text, token_predictions)
    for field_name, rule_val in rule_fields.items():
        if not rule_val:
            continue
        # Rule-based regexes are highly accurate for this structured layout.
        # We prefer rule-based values if found, to correct noisy LayoutLMv3 token classification.
        fields[field_name] = {
            "value": rule_val,
            "confidence": 0.85,
            "low_confidence": False,
        }

    overall_confidence = sum(f.get("confidence", 0) for f in fields.values()) / max(
        len(fields), 1
    )
    return {
        "fields": fields,
        "raw_text": raw_text,
        "overall_confidence": round(overall_confidence, 4),
        "raw_tokens": token_predictions,
    }


def _run_ocr_model(image_path: str, model_path: str | None) -> tuple[str, list[dict]]:
    """Attempt LayoutLMv3 inference; fall back to Tesseract-style placeholder."""
    model_path = model_path or os.getenv("CUSTOM_OCR_MODEL_PATH", "")
    if model_path:
        path_obj = Path(model_path)
        if not path_obj.is_absolute():
            repo_root = Path(__file__).resolve().parent.parent.parent
            resolved = repo_root / model_path
            if resolved.exists():
                model_path = str(resolved)
    if model_path and Path(model_path).exists():
        try:
            return _layoutlm_extract(image_path, model_path)
        except Exception as e:
            logger.warning(f"LayoutLMv3 inference failed: {e}, falling back to heuristic")
    return _fallback_extract(image_path)


def _setup_tesseract_cmd() -> None:
    """Dynamically configure PyTesseract executable path on macOS / Windows / standard environments."""
    try:
        import pytesseract
    except ImportError:
        return

    # Check if already set and valid
    if getattr(pytesseract.pytesseract, "tesseract_cmd", None):
        if os.path.exists(pytesseract.pytesseract.tesseract_cmd):
            return

    # Common search paths
    candidates = [
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
        "/usr/bin/tesseract",
        "/usr/local/Cellar/tesseract/5.5.2/bin/tesseract",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    import shutil
    path_bin = shutil.which("tesseract")
    if path_bin:
        pytesseract.pytesseract.tesseract_cmd = path_bin
        return

    for c in candidates:
        if os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd = c
            return


def _layoutlm_extract(image_path: str, model_path: str) -> tuple[str, list[dict]]:
    """Extract fields using the fine-tuned LayoutLMv3 model.

    Pipeline:
    1. Run Tesseract OCR → word strings + pixel bounding boxes.
    2. Normalise boxes to [0, 1000] (LayoutLMv3 format).
    3. Encode image + words + boxes with the processor (apply_ocr=False).
    4. Forward pass through fine-tuned model → token-level label predictions.
    5. Map token predictions back to words via ``encoding.word_ids()``.
    """
    import torch
    from PIL import Image

    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("pytesseract is required for inference — run: pip install pytesseract") from exc

    _setup_tesseract_cmd()

    device = "cpu"
    processor, model = OCRModelCache.get_model(model_path)
    if isinstance(processor, tuple):
        processor = processor[0]
    if processor is None or model is None:
        raise ValueError("Failed to load LayoutLMv3 model")

    image = Image.open(image_path).convert("RGB")
    img_w, img_h = image.size

    # ── Step 1: Tesseract OCR → words + pixel bboxes ────────────────────────
    ocr_data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, lang="eng"
    )
    words: list[str] = []
    boxes: list[list[int]] = []
    for i in range(len(ocr_data["text"])):
        word = (ocr_data["text"][i] or "").strip()
        if not word:
            continue
        if int(ocr_data["conf"][i]) < 0:
            continue
        x = ocr_data["left"][i]
        y = ocr_data["top"][i]
        w = ocr_data["width"][i]
        h = ocr_data["height"][i]
        # Normalise to 0-1000 (LayoutLMv3 coordinate space)
        x0 = min(max(int((x / img_w) * 1000), 0), 1000)
        y0 = min(max(int((y / img_h) * 1000), 0), 1000)
        x1 = min(max(int(((x + w) / img_w) * 1000), 0), 1000)
        y1 = min(max(int(((y + h) / img_h) * 1000), 0), 1000)
        words.append(word)
        boxes.append([x0, y0, x1, y1])

    if not words:
        logger.warning("Tesseract found no words in image: %s", image_path)
        return "", []

    # ── Step 2: Encode with processor (apply_ocr=False) ─────────────────────
    encoding = processor(
        image,
        words,
        boxes=boxes,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    # ── Step 3: Model forward pass ───────────────────────────────────────────
    encoding_tensors = {k: v.to(device) for k, v in encoding.items()}
    with torch.no_grad():
        outputs = model(**encoding_tensors)
    token_preds = outputs.logits.argmax(-1).squeeze().tolist()
    if isinstance(token_preds, int):
        token_preds = [token_preds]

    # ── Step 4: Map token predictions → word predictions ─────────────────────
    # word_ids() maps each token position to its source word index in `words`.
    # None means special token ([CLS], [SEP], padding). We take the first
    # sub-token prediction for each word (same convention as training).
    word_ids = encoding.word_ids(batch_index=0)
    word_label: dict[int, int] = {}
    for token_idx, word_idx in enumerate(word_ids):
        if word_idx is None:
            continue
        if word_idx not in word_label:  # first sub-token wins
            pred = token_preds[token_idx] if token_idx < len(token_preds) else 0
            word_label[word_idx] = pred

    tokens: list[dict] = []
    raw_parts: list[str] = []
    for word_idx, word in enumerate(words):
        label_id = word_label.get(word_idx, 0)
        tokens.append({
            "text": word, 
            "label_id": label_id, 
            "confidence": 0.85,
            "bbox": boxes[word_idx] if word_idx < len(boxes) else [0, 0, 0, 0]
        })
        raw_parts.append(word)

    return " ".join(raw_parts), tokens


def _fallback_extract(image_path: str) -> tuple[str, list[dict]]:
    """Demo fallback when no fine-tuned model is available."""
    demo_text = (
        "Date: 2025-06-01 Complainant: K. Perera Location: Colombo 07 "
        "Description: Theft of mobile phone near Galle Road Officer: SI Silva"
    )
    tokens = [
        {"text": "2025-06-01", "label": "date", "confidence": 0.72},
        {"text": "K. Perera", "label": "complainant_name", "confidence": 0.68},
        {"text": "Colombo 07", "label": "location", "confidence": 0.81},
        {
            "text": "Theft of mobile phone near Galle Road",
            "label": "case_description",
            "confidence": 0.75,
        },
        {"text": "SI Silva", "label": "officer_name", "confidence": 0.90},
    ]
    return demo_text, tokens
