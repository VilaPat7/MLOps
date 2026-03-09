import os
import pickle
import numpy as np
from pydantic import BaseModel, validator
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Pydantic модель для входных данных CIFAR-10
class CIFAR10Input(BaseModel):
    instances: List[List[List[List[float]]]]  # [batch, 32, 32, 3]

    @validator('instances')
    def check_shape(cls, v):
        for img in v:
            arr = np.array(img)
            if arr.shape != (32, 32, 3):
                raise ValueError("Каждое изображение должно быть размером 32x32x3")
        return v

class AnomalyDetector:
    """Загружает обученный детектор аномалий (например, из pickle)."""
    def __init__(self, model_path: str):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info("Детектор аномалий загружен")

    def predict(self, X: np.ndarray) -> np.ndarray:
        # Предполагаем, что модель возвращает 1 для аномалий, 0 для нормальных
        return self.model.predict(X)

# Инициализация детектора (будет вызвана при старте)
anomaly_detector = None
def init_anomaly_detector():
    global anomaly_detector
    detector_path = os.getenv("ANOMALY_DETECTOR_PATH", "/app/anomaly_detector.pkl")
    if os.path.exists(detector_path):
        anomaly_detector = AnomalyDetector(detector_path)
    else:
        logger.warning("Детектор аномалий не найден, проверка отключена")

def validate_input(data: dict) -> CIFAR10Input:
    """Проверка входных данных через Pydantic."""
    return CIFAR10Input(**data)

def detect_anomalies(images: np.ndarray) -> bool:
    """Возвращает True, если хотя бы одно изображение аномально."""
    if anomaly_detector is None:
        return False
    preds = anomaly_detector.predict(images)
    return np.any(preds == 1)

def preprocess(validated_input: CIFAR10Input) -> np.ndarray:
    """Нормализация изображений."""
    images = np.array(validated_input.instances, dtype=np.float32)
    images = images / 255.0
    return images

def postprocess(model_output: np.ndarray) -> dict:
    """
    Преобразует выход модели (логиты) в предсказанные классы и вероятности.
    model_output ожидается формы (batch, num_classes)
    """
    probabilities = tf.nn.softmax(model_output).numpy()
    predictions = np.argmax(probabilities, axis=1)
    return {
        "predictions": predictions.tolist(),
        "probabilities": probabilities.tolist()
    }
