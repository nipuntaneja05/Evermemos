import requests, os
from dotenv import load_dotenv
load_dotenv()
headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
print(resp.status_code)
if resp.status_code == 200:
    models = [m["id"] for m in resp.json()["data"]]
    print("Available models:", models)
else:
    print(resp.text)
