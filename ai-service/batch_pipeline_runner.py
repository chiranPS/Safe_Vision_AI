import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path
sys.path.append(os.getcwd())

os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_enable_new_executor'] = '0'
os.environ['PADDLE_PIR_ENABLE'] = '0'
os.environ['PADDLE_PIR_MODE'] = '0'

from app.services.pipeline import process_complaint_pipeline

async def run_batch():
    test_forms_dir = Path(r"e:\My work\Police-Compliant MS\ai-service\app\test_forms")
    if not test_forms_dir.exists():
        print(f"Error: {test_forms_dir} directory not found.")
        return
        
    form_paths = sorted(list(test_forms_dir.glob("*.png")))
    print(f"Found {len(form_paths)} forms to test.")
    
    results = {}
    
    for path in form_paths:
        name = path.name
        print(f"\nProcessing {name}...")
        try:
            res = await process_complaint_pipeline(path)
            results[name] = {
                "reference_number": res["complaint"]["referenceNumber"],
                "police_station": res["complaint"]["policeStation"],
                "date": res["complaint"]["date"],
                "complainant": {
                    "name": res["complainant"]["name"],
                    "nic": res["complainant"]["nic"],
                    "dob": res["complainant"]["dob"],
                    "phone": res["complainant"]["phone"],
                    "address": res["complainant"]["address"],
                    "gender": res["complainant"]["gender"]
                },
                "incident": {
                    "persons_involved": res["complaint"]["personsInvolved"],
                    "suspected_individuals": res["complaint"]["suspectedIndividuals"],
                    "vehicle_details": res["complaint"]["vehicleDetails"],
                    "location": res["complaint"]["location"]
                },
                "evidence": {
                    "hasPhotos": res["complaint"]["hasPhotos"],
                    "hasMedicalReport": res["complaint"]["hasMedicalReport"],
                    "hasCctv": res["complaint"]["hasCctv"],
                    "hasWitnessStatement": res["complaint"]["hasWitnessStatement"],
                    "hasAudioRecording": res["complaint"]["hasAudioRecording"],
                    "hasOtherEvidence": res["complaint"]["hasOtherEvidence"]
                }
            }
            print(f"  Ref: {results[name]['reference_number']}")
            print(f"  Station: {results[name]['police_station']}")
            print(f"  Name: {results[name]['complainant']['name']}")
            print(f"  Phone: {results[name]['complainant']['phone']}")
            print(f"  Addr: {results[name]['complainant']['address']}")
            print(f"  Persons: {results[name]['incident']['persons_involved']}")
            print(f"  Suspects: {results[name]['incident']['suspected_individuals']}")
            print(f"  Vehicles: {results[name]['incident']['vehicle_details']}")
        except Exception as e:
            print(f"  Failed to process {name}: {e}")
            
    # Write to batch_test_results.json
    output_file = Path("batch_test_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll results saved to {output_file.absolute()}")

if __name__ == "__main__":
    asyncio.run(run_batch())
