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

SHARED_MODEL_DIR = "/shared/models/cifar10_model/1"
TF_SERVING_HOST = "localhost:8500"

@app.on_event("startup")
async def startup_event():
    init_anomaly_detector()
    logger.info("Загрузка модели из MLflow...")
    try:
        prepare_model(target_dir=SHARED_MODEL_DIR)
        logger.info("✅ Модель успешно загружена и проверена")
        time.sleep(15)
        logger.info("Продолжаем запуск")
    except Exception as e:
        logger.error(f"❌ Не удалось подготовить модель: {e}")
        raise

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/v1/models/cifar10:predict")
async def predict(request: dict):
    # 1. Валидация
    try:
        validated = validate_input(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Неверный формат запроса: {e}")

    # 2. Предобработка
    try:
        images = preprocess(validated)
        logger.info(f"Preprocessed images shape: {images.shape}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка предобработки: {e}")

    # 3. Детекция аномалий
    try:
        if detect_anomalies(images):
            raise HTTPException(status_code=403, detail="Обнаружена аномалия в запросе")
    except Exception as e:
        logger.error(f"Ошибка в детекторе аномалий: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка безопасности")

    # 4. Отправка в TF Serving
    max_retries = 3
    for attempt in range(max_retries):
        try:
            channel = grpc.insecure_channel(TF_SERVING_HOST)
            stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

            request_tf = predict_pb2.PredictRequest()
            request_tf.model_spec.name = "cifar10_model"
            request_tf.model_spec.signature_name = "serving_default"

            input_name = "conv2d_input"
            output_name = "dense_1"

            request_tf.inputs[input_name].CopyFrom(
                tf.make_tensor_proto(images, dtype=tf.float32)
            )

            response = stub.Predict(request_tf, timeout=5.0)
            predictions = tf.make_ndarray(response.outputs[output_name])
            break
        except grpc.RpcError as e:
            logger.error(f"gRPC ошибка (попытка {attempt+1}/{max_retries}): {e.code()} - {e.details()}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=503, detail="Сервис предсказаний временно недоступен")
            time.sleep(2)
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
