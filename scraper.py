import os
import requests

API_KEY = os.environ["TRUTH_API_KEY"]
API_URL = os.environ["TRUTH_API_URL"]

response = requests.get(
    API_URL,
    params={
        "url": "https://truthsocial.com/@realDonaldTrump"
    },
    headers={
        "Authorization": f"Bearer {API_KEY}"
    },
    timeout=30
)

response.raise_for_status()

data = response.json()

print(data)
