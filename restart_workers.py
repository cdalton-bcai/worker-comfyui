import requests, json, time

API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
ENDPOINT_ID = "tfijj06nammf3v"
GQL_URL = "https://api.runpod.io/graphql"
HEADERS = {"Content-Type": "application/json", "api_key": API_KEY}

# Step 1: Get current endpoint config
query = """
query {
  myself {
    endpoints {
      id
      name
      templateId
      workersMin
      workersMax
      gpuIds
      idleTimeout
    }
  }
}
"""
r = requests.post(GQL_URL, headers=HEADERS, json={"query": query})
print("Endpoints:", json.dumps(r.json(), indent=2)[:2000])

# Find our endpoint
data = r.json().get("data", {}).get("myself", {}).get("endpoints", [])
endpoint = None
for ep in data:
    if ep.get("id") == ENDPOINT_ID:
        endpoint = ep
        break

if endpoint:
    print(f"\nFound endpoint: {endpoint['name']}")
    print(f"  Min workers: {endpoint['workersMin']}")
    print(f"  Max workers: {endpoint['workersMax']}")
    
    # Step 2: Scale to 0 to force worker recycling
    print("\nScaling to 0 workers...")
    mutation = """
    mutation {{
      saveEndpoint(input: {{
        id: "{id}"
        workersMin: 0
        workersMax: 0
      }}) {{
        id
        workersMin
        workersMax
      }}
    }}
    """.format(id=ENDPOINT_ID)
    r2 = requests.post(GQL_URL, headers=HEADERS, json={"query": mutation})
    print(f"Scale down: {r2.status_code} {r2.text[:500]}")
    
    # Wait for workers to drain
    print("Waiting 15s for workers to drain...")
    time.sleep(15)
    
    # Step 3: Scale back up
    print(f"\nScaling back to min={endpoint['workersMin']} max={endpoint['workersMax']}...")
    mutation2 = """
    mutation {{
      saveEndpoint(input: {{
        id: "{id}"
        workersMin: {wmin}
        workersMax: {wmax}
      }}) {{
        id
        workersMin
        workersMax
      }}
    }}
    """.format(id=ENDPOINT_ID, wmin=endpoint['workersMin'], wmax=endpoint['workersMax'])
    r3 = requests.post(GQL_URL, headers=HEADERS, json={"query": mutation2})
    print(f"Scale up: {r3.status_code} {r3.text[:500]}")
    print("\nDone! Workers will restart with the new v4-lustify image.")
else:
    print(f"\nEndpoint {ENDPOINT_ID} not found in your account.")
