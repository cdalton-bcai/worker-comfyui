import requests, json, time

API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
ENDPOINT = "tfijj06nammf3v"
URL = f"https://api.runpod.ai/v2/{ENDPOINT}"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

with open("test_input_sdxl.json") as f:
    payload = json.load(f)

print("Submitting job...")
r = requests.post(f"{URL}/run", headers=HEADERS, json=payload)
resp = r.json()
job_id = resp.get("id")
print(f"Job ID: {job_id}")

if not job_id:
    print(f"Error: {resp}")
    exit(1)

for i in range(90):
    time.sleep(5)
    r2 = requests.get(f"{URL}/status/{job_id}", headers=HEADERS)
    sd = r2.json()
    st = sd.get("status", "UNKNOWN")
    print(f"  [{(i+1)*5}s] {st}")
    if st == "COMPLETED":
        output = sd.get("output", {})
        if isinstance(output, dict):
            images = output.get("images", [])
            print(f"  SUCCESS - {len(images)} image(s) returned")
            for img in images[:1]:
                if isinstance(img, dict):
                    print(f"  Image: {str(img)[:300]}")
                else:
                    print(f"  Image data length: {len(str(img))}")
        else:
            print(f"  Output: {str(output)[:500]}")
        break
    elif st == "FAILED":
        print(f"  FAILED: {sd.get('error', 'unknown')}")
        break
