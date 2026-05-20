#!/usr/bin/env python3
import requests
import numpy as np

data = np.load("adv_examples.npz")
x_adv = data['x_adv']

# Если JWT отключён, заголовок Authorization не нужен
# Если JWT включён, раскомментируйте следующую строку и замените токен
# TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImRlbW8iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2NsdXN0ZXIubG9jYWwiLCJzdWIiOiJlbWFpbEBleGFtcGxlLmNvbSIsImVtYWlsIjoiZW1haWxAZXhhbXBsZS5jb20iLCJncm91cHMiOlsiZ3JvdXAxIiwiZ3JvdXAyIl0sIm5hbWUiOiJKb2huIERvZSIsImlhdCI6MTUxNjIzOTAyMn0.kMuAYrCj8f0gUjvFyWz--TzEnaqjuy4XKzJpL4GdKQx6rOqPkO9z5jJQo7qWv3mXhRfFQbY1k9cGfNlM"
# headers = {"Authorization": f"Bearer {TOKEN}"}
headers = {"Content-Type": "application/json"}   # без JWT

rejected = 0
total = len(x_adv)
for i, img in enumerate(x_adv):
    payload = {"instances": [img.tolist()]}
    try:
        resp = requests.post("http://localhost:8080/v1/models/cifar10:predict",
                             json=payload, headers=headers, timeout=5)
        if resp.status_code != 200:
            rejected += 1
    except Exception:
        rejected += 1

print(f"Rejected {rejected}/{total} ({rejected/total*100:.2f}%)")
