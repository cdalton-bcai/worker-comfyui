import requests, json

API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
GQL_URL = "https://api.runpod.io/graphql"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

# Get endpoint details including template
query = """
query {
  myself {
    endpoints {
      id
      name
      templateId
      template {
        id
        name
        imageName
        containerDiskInGb
        volumeInGb
        env {
          key
          value
        }
      }
      workersMin
      workersMax
      gpuIds
    }
  }
}
"""

r = requests.post(GQL_URL, headers=HEADERS, json={"query": query})
data = r.json()
print(json.dumps(data, indent=2))
