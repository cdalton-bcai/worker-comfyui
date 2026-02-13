import requests
import json
import base64
import os
import time
import sys

API_KEY = "rpa_C0DVYI5FODZT1X9V1J1BN7HSCI3Z02350B7O836N3sw101"
ENDPOINT_ID = "tfijj06nammf3v"

def run_test(config_file, output_name):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found.")
        return False

    with open(config_file, 'r') as f:
        payload = json.load(f)

    print(f"Submitting job from {config_file}...")
    run_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
    response = requests.post(run_url, headers=headers, json=payload)
    job_data = response.json()
    job_id = job_data.get("id")
    print(f"Job ID: {job_id}")

    status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"
    
    while True:
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        status = status_data.get("status")
        print(f"Status: {status}")
        
        if status == "COMPLETED":
            print("Job completed. Saving image...")
            output = status_data.get("output", {})
            if isinstance(output, dict) and "images" in output:
                images = output["images"]
                if images:
                    img_obj = images[0]
                    image_b64 = img_obj.get("data") or img_obj.get("image")
                    if image_b64:
                        image_data = base64.b64decode(image_b64)
                        with open(output_name, "wb") as f:
                            f.write(image_data)
                        print(f"Successfully saved to {output_name}")
                        print(f"Size: {len(image_data)} bytes")
                        return True
            print("No image data found in response.")
            return False
        elif status == "FAILED":
            print("Job failed.")
            print(json.dumps(status_data, indent=2))
            return False
        
        time.sleep(10)

if __name__ == "__main__":
    config = "test_input_v2.json"
    output = "test_output_latest.png"
    
    if len(sys.argv) > 1:
        config = sys.argv[1]
    if len(sys.argv) > 2:
        output = sys.argv[2]
        
    run_test(config, output)

