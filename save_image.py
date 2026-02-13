import requests
import json
import base64
import os

API_KEY = "rpa_C0DVYI5FODZT1X9V1J1BN7HSCI3Z02350B7O836N3sw101"
ENDPOINT_ID = "tfijj06nammf3v"
JOB_ID = "d9119a72-95d1-4c83-b6d1-494b2515a758-u1"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{JOB_ID}"

print(f"Fetching status for job {JOB_ID}...")
response = requests.get(url, headers=headers)
data = response.json()

if data.get("status") == "COMPLETED":
    print("Job completed. Saving image...")
    images = data.get("output", {}).get("images", [])
    if images:
        image_b64 = images[0].get("image")
        if image_b64:
            image_data = base64.b64decode(image_b64)
            output_path = r"C:\Users\cgdal\Documents\GitHub\worker-comfyui\test_output_fixed.png"
            with open(output_path, "wb") as f:
                with open(output_path, "wb") as f:
                    f.write(image_data)
            print(f"Successfully saved to {output_path}")
            print(f"File size: {os.path.getsize(output_path)} bytes")
        else:
            print("No image data found in response.")
    else:
        print("No images array found in output.")
else:
    print(f"Job status is {data.get('status')}")
    print(json.dumps(data, indent=2))
