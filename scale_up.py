import requests, json

API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
GQL_URL = "https://api.runpod.io/graphql"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

mutation = """
mutation {
  saveEndpoint(input: {
    id: "tfijj06nammf3v"
    name: "acceptable_purple_panther"
    workersMax: 3
  }) {
    id
    workersMax
  }
}
"""

r = requests.post(GQL_URL, headers=HEADERS, json={"query": mutation})
print(json.dumps(r.json(), indent=2))
