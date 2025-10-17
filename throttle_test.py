import time

import requests

BASE_URL = "http://localhost"

response = requests.post(f"{BASE_URL}/api/token/", json={"username": "admin", "password": "admin"})
tokens = response.json()
access_token = tokens["access"]
refresh_token = tokens["refresh"]

start = time.perf_counter()



headers = {"Authorization": f"Bearer {access_token}"}
req_number = 1000

success = 0
fail = 0

for i in range(req_number):
    response = requests.post(f"{BASE_URL}/api/validate/", headers=headers, json={"national_id": "29801011401891"})
    if response.status_code == 200:
        success+=1
    else:
        fail +=1




end = time.perf_counter()
total = end - start

print(f"Total time for {req_number} requests: {total:.2f} seconds")
print(f"Average per request: {total / req_number:.4f} seconds")
print(f"Success requests: {success} , Fail requests : {fail} , Total : {success+fail}")

