import os
from mlflow import MlflowClient

# ID запуска (run_id) — возьмите из UI или из URI модели
run_id = "0544b6cf676b466eb4e12bff72ed22a6"

# Локальный путь к файлу подписи
local_path = os.path.expanduser("~/mlops-infra/docker/gates/gate4_signature_verify/signature.sig")

# Путь внутри артефактов, куда положить файл (папка model)
artifact_path = "model"

# Создаём клиента
client = MlflowClient()

# Загружаем артефакт
client.log_artifact(run_id, local_path, artifact_path)
print(f"Файл {local_path} успешно загружен в run {run_id}, путь: {artifact_path}")
