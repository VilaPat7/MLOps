import os
import logging
import tempfile
import shutil
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient
import tensorflow as tf
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_public_key(key_path: str):
    """Загружает публичный ключ из файла."""
    with open(key_path, "rb") as key_file:
        public_key = load_pem_public_key(key_file.read())
    return public_key

def compute_model_hash(model_path: str) -> bytes:
    """Вычисляет SHA256 хеш всех файлов в папке модели."""
    import hashlib
    hasher = hashlib.sha256()
    for root, _, files in os.walk(model_path):
        for file in sorted(files):  # сортируем для детерминизма
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                hasher.update(f.read())
    return hasher.digest()

def verify_model_signature(model_path: str, signature_path: str, public_key) -> bool:
    """Проверяет подпись модели."""
    model_hash = compute_model_hash(model_path)
    with open(signature_path, "rb") as sig_file:
        signature = sig_file.read()
    try:
        public_key.verify(
            signature,
            model_hash,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        logger.info("✅ Подпись модели верна")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка проверки подписи: {e}")
        return False

def download_model_from_registry(model_name: str, stage: str, dst_dir: str):
    """
    Загружает артефакты модели из MLflow Model Registry.
    Возвращает путь к папке с моделью и путь к файлу подписи.
    """
    client = MlflowClient()
    latest_version = client.get_latest_versions(model_name, stages=[stage])
    if not latest_version:
        raise RuntimeError(f"Нет модели {model_name} в стадии {stage}")
    run_id = latest_version[0].run_id
    artifact_uri = latest_version[0].source  # например "s3://bucket/.../artifacts/model"

    logger.info(f"Загружаем модель из {artifact_uri}")
    # Скачиваем артефакты во временную папку
    local_path = mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri, dst_path=dst_dir)
    # local_path указывает на корень артефактов (папка model)
    model_path = local_path

    signature_path = os.path.join(model_path, "signature.sig")
    if not os.path.exists(signature_path):
        raise FileNotFoundError("Файл подписи не найден")
    return model_path, signature_path

def prepare_model(target_dir: str = "/shared/models/1"):
    """
    Основная функция: загружает модель, проверяет подпись и сохраняет в target_dir.
    Вызывается при старте контейнера.
    """
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-server.mlflow-system.svc.cluster.local:5000")
    model_name = os.getenv("MLFLOW_MODEL_NAME", "cifar10_model")
    model_stage = os.getenv("MLFLOW_MODEL_STAGE", "Production")
    public_key_path = os.getenv("PUBLIC_KEY_PATH", "/app/keys/public_key.pem")

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    public_key = load_public_key(public_key_path)

    # Создаём временную директорию для загрузки
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path, signature_path = download_model_from_registry(model_name, model_stage, tmpdir)

        if not verify_model_signature(model_path, signature_path, public_key):
            raise RuntimeError("Модель не прошла проверку подписи (Gate 4)")

        # Копируем модель в целевую директорию (ожидается, что target_dir пуст или перезаписываем)
        os.makedirs(target_dir, exist_ok=True)
        # Предполагаем, что модель сохранена в формате SavedModel
        # В model_path должна быть папка с моделью (например, содержащая saved_model.pb)
        # Копируем содержимое
        for item in os.listdir(model_path):
            s = os.path.join(model_path, item)
            d = os.path.join(target_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        logger.info(f"Модель скопирована в {target_dir}")
        return target_dir
