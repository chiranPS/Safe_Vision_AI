import sys
try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    print("PaddleOCR loaded successfully.")
except Exception as e:
    print(f"Error loading PaddleOCR: {e}")
    sys.exit(1)
