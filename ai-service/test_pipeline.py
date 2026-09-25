
import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

# Disable PIR and oneDNN to prevent crashes on Windows with PaddlePaddle 3.x
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_enable_new_executor'] = '0'
os.environ['PADDLE_PIR_ENABLE'] = '0'
os.environ['PADDLE_PIR_MODE'] = '0'

from app.services.pipeline import process_complaint_pipeline

async def main():
    test_file = Path("test_complaint.png")
    if not test_file.exists():
        print(f"Error: {test_file} not found.")
        return

    print(f"--- Starting Pipeline for {test_file} ---")
    try:
        result = await process_complaint_pipeline(test_file)
        print("\n--- Extraction Result ---")
        print(json.dumps(result, indent=2))
        
        # Save result to a file for review
        with open("test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResult saved to test_result.json")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
