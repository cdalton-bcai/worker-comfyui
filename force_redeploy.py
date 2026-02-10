import requests, json, time

API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
ENDPOINT_ID = "tfijj06nammf3v"
GQL_URL = "https://api.runpod.io/graphql"
REST_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
GQL_HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
REST_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Step 1: Get full endpoint config
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
      scalerType
      scalerValue
    }
  }
}
"""
r = requests.post(GQL_URL, headers=GQL_HEADERS, json={"query": query})
endpoints = r.json()["data"]["myself"]["endpoints"]
ep = next(e for e in endpoints if e["id"] == ENDPOINT_ID)
print(f"Current config: {json.dumps(ep, indent=2)}")

# Step 2: Scale to 0 max workers
print("\n--- Scaling to 0 max workers ---")
mutation_down = """
mutation {
  saveEndpoint(input: {
    id: "%s"
    name: "%s"
    templateId: "%s"
    gpuIds: "%s"
    workersMin: 0
    workersMax: 0
    idleTimeout: %d
    scalerType: "%s"
    scalerValue: %d
  }) {
    id
    workersMin
    workersMax
  }
}
""" % (ep["id"], ep["name"], ep["templateId"], ep["gpuIds"],
       ep.get("idleTimeout", 5), ep.get("scalerType", "QUEUE_DELAY"),
       ep.get("scalerValue", 1))

r2 = requests.post(GQL_URL, headers=GQL_HEADERS, json={"query": mutation_down})
print(f"Result: {json.dumps(r2.json(), indent=2)}")

# Step 3: Wait for all workers to drain
print("\n--- Waiting for workers to drain ---")
for i in range(24):
    time.sleep(5)
    h = requests.get(f"{REST_URL}/health", headers=REST_HEADERS).json()
    w = h.get("workers", {})
    total = w.get("idle", 0) + w.get("running", 0) + w.get("initializing", 0)
    print(f"  [{(i+1)*5}s] idle={w.get('idle',0)} running={w.get('running',0)} init={w.get('initializing',0)} throttled={w.get('throttled',0)}")
    if total == 0:
        print("  All workers drained!")
        break

# Step 4: Scale back up
print("\n--- Scaling back to original config ---")
mutation_up = """
mutation {
  saveEndpoint(input: {
    id: "%s"
    name: "%s"
    templateId: "%s"
    gpuIds: "%s"
    workersMin: %d
    workersMax: %d
    idleTimeout: %d
    scalerType: "%s"
    scalerValue: %d
  }) {
    id
    workersMin
    workersMax
  }
}
""" % (ep["id"], ep["name"], ep["templateId"], ep["gpuIds"],
       ep.get("workersMin", 0), ep.get("workersMax", 3),
       ep.get("idleTimeout", 5), ep.get("scalerType", "QUEUE_DELAY"),
       ep.get("scalerValue", 1))

r3 = requests.post(GQL_URL, headers=GQL_HEADERS, json={"query": mutation_up})
print(f"Result: {json.dumps(r3.json(), indent=2)}")
print("\nDone! Workers will now pull the v4-lustify image fresh.")
