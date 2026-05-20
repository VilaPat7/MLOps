import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np

app = FastAPI()

class PredictRequest(BaseModel):
    instances: List[List[List[List[float]]]]

@app.post("/v1/models/cifar10:predict")
async def predict(request: PredictRequest):
    # С вероятностью 90% отклоняем запрос (аномалия)
    if random.random() < 0.9:
        raise HTTPException(status_code=403, detail="Anomaly detected")
    # Иначе возвращаем фиктивное предсказание (класс 5)
    return {"predictions": [5]}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/v1/models/cifar10")
async def model_info():
    return {"model_version_status": [{"version": "1", "state": "AVAILABLE"}]}
