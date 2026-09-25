import asyncio
import logging
from pathlib import Path
from app.services.pipeline import process_complaint_pipeline
import json

logging.basicConfig(level=logging.ERROR)

async def main():
    forms = [
        "test-form-12.png",
        "test-form-13.png",
    ]
    base_path = Path(r"E:\My work\Police-Compliant MS\SafeVisionAI\data\raw_forms\police_forms")
    
    results = {}
    for form in forms:
        path = base_path / form
        if not path.exists():
            continue
        try:
            res = await process_complaint_pipeline(path)
            results[form] = res
        except Exception as e:
            print(f"Error on {form}: {e}")
            
    with open("batch_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("Done writing batch_results.json")

if __name__ == "__main__":
    asyncio.run(main())
