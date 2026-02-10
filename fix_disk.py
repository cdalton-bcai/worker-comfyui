import requests, json

API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
GQL_URL = "https://api.runpod.io/graphql"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

# Update template to increase container disk
mutation = """
mutation {
  saveTemplate(input: {
    id: "23my5u43nn"
    name: "sdx1-initial"
    imageName: "cdaltonbcai/comfyui-sdxl:v4-lustify"
    containerDiskInGb: 40
    volumeInGb: 0
    dockerArgs: ""
    env: []
    isServerless: true
  }) {
    id
    name
    imageName
    containerDiskInGb
  }
}
"""

r = requests.post(GQL_URL, headers=HEADERS, json={"query": mutation})
print(json.dumps(r.json(), indent=2))
