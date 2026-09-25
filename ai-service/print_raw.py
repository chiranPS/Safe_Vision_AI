import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from app.services.safevision_ocr.extractor import extract_fields

async def main():
    test_file = Path("test_complaint.png")
    res = extract_fields(str(test_file))
    print("=== RAW TEXT ===")
    print(res["raw_text"])
    print("=== FIELDS ===")
    import json
    print(json.dumps(res["fields"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
