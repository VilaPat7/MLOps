import os
import pickle
import numpy as np
import tensorflow as tf
from pydantic import BaseModel, validator
from typing import List, Optional
import logging
import random



logger = logging.getLogger(__name__)

class CIFAR10Input(BaseModel):
    instances: List[List[List[List[float]]]]  # [batch, 32, 32, 3]

    @validator('instances')
    def check_shape(cls, v):
        for img in v:
            arr = np.array(img)
            if arr.shape != (32, 32, 3):
                raise ValueError("Each image must be sized 32x32x3")
        return v

class AnomalyDetector:
    def __init__(self, model_path: str):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info("Anomaly detector is loaded")

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

anomaly_detector = None
def init_anomaly_detector():
    global anomaly_detector
    detector_path = os.getenv("ANOMALY_DETECTOR_PATH", "/app/anomaly_detector.pkl")
    if os.path.exists(detector_path):
        anomaly_detector = AnomalyDetector(detector_path)
    else:
        logger.warning("Anomaly detector not found, verification disabled")

def validate_input(data: dict) -> CIFAR10Input:
    return CIFAR10Input(**data)

def detect_anomalies(images):
    return random.random() < 0.9

def preprocess(validated_input: CIFAR10Input) -> np.ndarray:
    images = np.array(validated_input.instances, dtype=np.float32)
    images = images / 255.0
    return images

def postprocess(model_output: np.ndarray) -> dict:
    probabilities = tf.nn.softmax(model_output).numpy()
    predictions = np.argmax(probabilities, axis=1)
    return {
        "predictions": predictions.tolist(),
        "probabilities": probabilities.tolist()
    }
