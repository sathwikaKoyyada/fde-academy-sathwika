import requests, time

start = time.time()
r = requests.post("http://127.0.0.1:8000/analytics/refresh")
print(f"POST returned in {time.time() - start:.2f}s, status {r.status_code}")

print(requests.get("http://127.0.0.1:8000/analytics/refresh-status").json())

time.sleep(6)
print(requests.get("http://127.0.0.1:8000/analytics/refresh-status").json())
