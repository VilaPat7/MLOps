import os
import logging
import time
import grpc
import numpy as np
import tensorflow as tf
from fastapi import FastAPI, HTTPException
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

from model_loader import prepare_model
from prepost_processor import (
    init_anomaly_detector, validate_input,
    preprocess, detect_anomalies, postprocess
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Константы
SHARED_MODEL_DIR = "/shared/models/1"
TF_SERVING_HOST = "localhost:8500"  # gRPC порт TF Serving

@app.on_event("startup")
async def startup_event():
    # 1. Инициализируем детектор аномалий
    init_anomaly_detector()

    # 2. Загружаем модель из MLflow и проверяем подпись
    logger.info("Загрузка модели из MLflow...")
    try:
        prepare_model(target_dir=SHARED_MODEL_DIR)
        logger.info("✅ Модель успешно загружена и проверена")
    except Exception as e:
        logger.error(f"❌ Не удалось подготовить модель: {e}")
        # Можно завершить контейнер, чтобы Kubernetes перезапустил под
        raise

    # 3. Ожидаем, пока TensorFlow Serving загрузит модель (он запускается параллельно)
    # Для простоты подождём несколько секунд и проверим доступность
    time.sleep(5)
    # Здесь можно добавить более надёжную проверку через gRPC health check

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/v1/models/cifar10:predict")
async def predict(request: dict):
    # 1. Валидация через Pydantic
    try:
        validated = validate_input(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Неверный формат запроса: {e}")

    # 2. Предобработка
    try:
        images = preprocess(validated)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка предобработки: {e}")

    # 3. Детекция аномалий (Gate 5)
    try:
        if detect_anomalies(images):
            raise HTTPException(status_code=403, detail="Обнаружена аномалия в запросе")
    except Exception as e:
        logger.error(f"Ошибка в детекторе аномалий: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка безопасности")

    # 4. Отправка запроса в TensorFlow Serving через gRPC
    try:
        # Создаём gRPC канал и stub
        channel = grpc.insecure_channel(TF_SERVING_HOST)
        stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

        # Формируем запрос
        request_tf = predict_pb2.PredictRequest()
        request_tf.model_spec.name = "cifar10_model"
        request_tf.model_spec.signature_name = "serving_default"

        # Добавляем входной тензор (ожидаем, что модель принимает float32 изображения)
        # Предполагаем, что вход называется "input_1" или "input" – нужно уточнить по модели
        # Можно автоматически получить из сигнатуры, но для простоты зададим константу
        input_name = "input_1"  # Замените на реальное имя входа вашей модели
        request_tf.inputs[input_name].CopyFrom(
            tf.make_tensor_proto(images, dtype=tf.float32)
        )

        # Вызов
        response = stub.Predict(request_tf, timeout=5.0)
        # Извлечение предсказаний: предположим выход называется "output_0" или "dense"
        output_name = "output_0"  # Замените на реальное имя выхода
        predictions = tf.make_ndarray(response.outputs[output_name])

    except grpc.RpcError as e:
        logger.error(f"gRPC ошибка: {e}")
        raise HTTPException(status_code=503, detail="Сервис предсказаний временно недоступен")
    except Exception as e:
        logger.error(f"Ошибка при обращении к TF Serving: {e}")
        raise HTTPException(status_code=500, detail="Ошибка выполнения модели")

    # 5. Постобработка
    result = postprocess(predictions)
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
