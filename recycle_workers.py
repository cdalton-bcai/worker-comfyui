import requests, json, time

API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
ENDPOINT_ID = "tfijj06nammf3v"
GQL_URL = "https://api.runpod.io/graphql"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

def update_endpoint(max_workers):
    mutation = 'mutation { saveEndpoint(input: { id: "%s", workersMax: %d }) { id workersMin workersMax } }' % (ENDPOINT_ID, max_workers)
    r = requests.post(GQL_URL, headers=HEADERS, json={"query": mutation})
    return r.json()

def get_health():
    r = requests.get(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/health",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return r.json()

# Step 1: Scale down to 0
print("Scaling max workers to 0...")
result = update_endpoint(0)
print(f"  Result: {json.dumps(result)}")

# Step 2: Wait for workers to drain
print("\nWaiting for workers to drain...")
for i in range(12):
    time.sleep(5)
    health = get_health()
    workers = health.get("workers", {})
    total = workers.get("idle", 0) + workers.get("running", 0) + workers.get("initializing", 0)
    print(f"  [{(i+1)*5}s] Workers: idle={workers.get('idle',0)} running={workers.get('running',0)} init={workers.get('initializing',0)}")
    if total == 0:
        print("  All workers drained!")
        break

# Step 3: Scale back up
print("\nScaling max workers back to 3...")
result = update_endpoint(3)
print(f"  Result: {json.dumps(result)}")

print("\nDone! New workers will pull v4-lustify image on next request.")
