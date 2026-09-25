from docling.document_converter import DocumentConverter
from pathlib import Path
import sys

def test_docling_ocr(image_path):
    try:
        converter = DocumentConverter()
        result = converter.convert(image_path)
        print("Text extracted successfully!")
        print(result.document.export_to_markdown())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_docling_ocr(sys.argv[1])
