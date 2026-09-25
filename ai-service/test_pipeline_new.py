import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from app.services.pipeline import process_complaint_pipeline

logging.basicConfig(level=logging.INFO)

async def main():
    test_file = Path(r"E:\My work\Police-Compliant MS\SafeVisionAI\data\raw_forms\police_forms\test-form-12.png")
    if not test_file.exists():
        print("test-form-12.png not found.")
        return
        
    try:
        result = await process_complaint_pipeline(test_file)
        print("Pipeline Result:")
        for key, value in result.items():
            if key == "complaint":
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            elif key == "complainant":
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
