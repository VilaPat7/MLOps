import os
import logging
import tempfile
import shutil
import boto3
from botocore.client import Config
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_public_key(key_path: str):
    with open(key_path, "rb") as key_file:
        public_key = load_pem_public_key(key_file.read())
    return public_key

def compute_model_hash(model_path: str) -> bytes:
    import hashlib
    hasher = hashlib.sha256()
    for root, _, files in os.walk(model_path):
        for file in sorted(files):
            if file == "signature.sig":          # <-- обязательно
                continue
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                hasher.update(f.read())
    hash_bytes = hasher.digest()
    print(f"[DEBUG] Model hash (hex): {hash_bytes.hex()}")   # <-- добавить
    return hash_bytes

def verify_model_signature(model_path: str, signature_path: str, public_key) -> bool:
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
        logger.error(f"❌ Ошибка проверки подписи: {e}", exc_info=True)
        return False

def download_from_minio(bucket: str, prefix: str, local_dir: str):
    """Скачивает все файлы из MinIO по указанному префиксу в локальную папку, сохраняя структуру."""
    logger.info(f"Скачиваем из MinIO bucket={bucket}, prefix={prefix}")
    s3_endpoint = os.getenv("MLFLOW_S3_ENDPOINT_URL")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    s3 = boto3.client(
        's3',
        endpoint_url=s3_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        verify=False
    )
    
    # Добавляем завершающий слэш, если его нет
    if not prefix.endswith('/'):
        prefix = prefix + '/'
    
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    
    file_count = 0
    for page in pages:
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            key = obj['Key']
            # Относительный путь внутри префикса
            if key.startswith(prefix):
                rel_path = key[len(prefix):]
            else:
                rel_path = key
            if not rel_path:   # пропускаем сам префикс
                continue
            local_file = os.path.join(local_dir, rel_path)
            os.makedirs(os.path.dirname(local_file), exist_ok=True)
            s3.download_file(bucket, key, local_file)
            file_count += 1
            logger.info(f"Скачан {key} -> {local_file}")
    logger.info(f"Всего скачано файлов: {file_count}")

def prepare_model(target_dir: str = "/shared/models/1"):
    """Загружает модель и подпись из MinIO, проверяет подпись и копирует в target_dir."""
    public_key_path = os.getenv("PUBLIC_KEY_PATH", "/app/keys/public_key.pem")
    public_key = load_public_key(public_key_path)
    
    bucket = os.getenv("MLFLOW_S3_BUCKET", "mlflow")
    prefix = os.getenv("MLFLOW_MODEL_PREFIX")
    if not prefix:
        raise ValueError("Переменная MLFLOW_MODEL_PREFIX не задана. Укажите путь к модели в MinIO.")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger.info(f"Скачиваем модель из MinIO: bucket={bucket}, prefix={prefix}")
        download_from_minio(bucket, prefix, tmpdir)
        
        model_path = tmpdir
        signature_path = os.path.join(model_path, "signature.sig")
        
        if not os.path.exists(signature_path):
            raise FileNotFoundError(f"Файл подписи не найден в MinIO по пути {prefix}/signature.sig")
        
        if not verify_model_signature(model_path, signature_path, public_key):
            raise RuntimeError("Модель не прошла проверку подписи (Gate 4)")
        
        # Копируем в целевую директорию
        os.makedirs(target_dir, exist_ok=True)
        for item in os.listdir(model_path):
            s = os.path.join(model_path, item)
            d = os.path.join(target_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        logger.info(f"✅ Модель скопирована в {target_dir}")
        return target_dir
