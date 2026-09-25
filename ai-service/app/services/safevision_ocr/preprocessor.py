"""OpenCV preprocessing for police form images."""

from __future__ import annotations

import cv2
import numpy as np


def preprocess(image_path: str) -> np.ndarray:
    """Read and return the image to preserve visual quality for LayoutLMv3 and Tesseract."""
    image = cv2.imread(image_path)
    if image is None:
        image = _read_with_pillow(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    return image



def _read_with_pillow(image_path: str) -> np.ndarray | None:
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            rgb = img.convert("RGB")
            return cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def _deskew(image: np.ndarray) -> np.ndarray:
    # Invert the binary image if the background is light (mean > 127)
    # so that text is white (255) and background is black (0) for correct deskew angle.
    if np.mean(image) > 127:
        inverted = cv2.bitwise_not(image)
    else:
        inverted = image

    coords = np.column_stack(np.where(inverted > 0))
    if len(coords) < 10:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5:
        return image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
