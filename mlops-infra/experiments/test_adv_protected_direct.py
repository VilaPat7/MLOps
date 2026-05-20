import requests
import numpy as np

data = np.load("adv_examples.npz")
x_adv = data['x_adv']

rejected = 0
total = len(x_adv)
for img in x_adv:
    payload = {"instances": [img.tolist()]}
    try:
        resp = requests.post("http://localhost:8084/v1/models/cifar10:predict", json=payload, timeout=5)
        if resp.status_code != 200:
            rejected += 1
    except:
        rejected += 1
print(f"Rejected {rejected}/{total} ({rejected/total*100:.2f}%)")
