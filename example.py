import pprint

import requests

# Base URL
BASE_URL = "http://localhost"

# Login
response = requests.post(f"{BASE_URL}/api/token/", json={"username": "admin", "password": "admin"})
tokens = response.json()
access_token = tokens["access"]
refresh_token = tokens["refresh"]

# Validate National ID
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(f"{BASE_URL}/api/validate/", headers=headers, json={"national_id": "29801011401891"})
result = response.json()
pprint.pprint(result)
