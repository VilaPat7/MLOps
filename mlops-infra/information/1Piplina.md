1. Сначала создадим необходимые образы:
Dockerfile для обучения:
dockerfile
# ~/mlops-infra/docker/train/Dockerfile
FROM tensorflow/tensorflow:2.13.0-gpu
RUN pip install mlflow==2.9.0 minio pandas numpy
COPY train.py /train.py
ENTRYPOINT ["python", "/train.py"]
Dockerfile для деплоя:
dockerfile
# ~/mlops-infra/docker/deploy/Dockerfile
FROM bitnami/kubectl:latest
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/*
COPY deploy.sh /deploy.sh
RUN chmod +x /deploy.sh
ENTRYPOINT ["/deploy.sh"]
2. Скрипт обучения:
python
# ~/mlops-infra/docker/train/train.py
import mlflow
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import os
import sys

def main():
    # Параметры обучения
    epochs = 5  # Для baseline можно меньше эпох
    batch_size = 64
    
    # Настройка MLflow
    mlflow.set_tracking_uri("http://mlflow-server.mlflow-system.svc.cluster.local:5000")
    mlflow.set_experiment("cifar10-baseline")
    
    # Загрузка данных CIFAR-10
    print("Loading CIFAR-10 dataset...")
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    
    # Нормализация
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    
    # Конвертация меток
    y_train = tf.keras.utils.to_categorical(y_train, 10)
    y_test = tf.keras.utils.to_categorical(y_test, 10)
    
    # Создание модели CNN
    print("Creating CNN model...")
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(10, activation='softmax')
    ])
    
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    # Начало MLflow run
    with mlflow.start_run() as run:
        print(f"MLflow Run ID: {run.info.run_id}")
        
        # Логирование параметров
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("dataset", "CIFAR-10")
        mlflow.log_param("model_type", "CNN")
        
        # Обучение модели
        print("Training model...")
        history = model.fit(x_train, y_train,
                          epochs=epochs,
                          batch_size=batch_size,
                          validation_split=0.2,
                          verbose=1)
        
        # Оценка модели
        test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
        print(f"Test accuracy: {test_acc:.4f}")
        
        # Логирование метрик
        mlflow.log_metric("test_accuracy", test_acc)
        mlflow.log_metric("test_loss", test_loss)
        
        # Логирование метрик по эпохам
        for epoch in range(epochs):
            mlflow.log_metric("train_accuracy", history.history['accuracy'][epoch], step=epoch)
            mlflow.log_metric("val_accuracy", history.history['val_accuracy'][epoch], step=epoch)
            mlflow.log_metric("train_loss", history.history['loss'][epoch], step=epoch)
            mlflow.log_metric("val_loss", history.history['val_loss'][epoch], step=epoch)
        
        # Сохранение модели в MLflow
        print("Saving model to MLflow...")
        mlflow.tensorflow.log_model(model, "model",
                                   registered_model_name="cifar10-cnn-baseline")
        
        # Сохраняем run_id для деплоя
        with open("/tmp/run_id.txt", "w") as f:
            f.write(run.info.run_id)
        
        print("Training completed successfully!")

if __name__ == "__main__":
    main()
3. Скрипт деплоя:
bash
#!/bin/bash
# ~/mlops-infra/docker/deploy/deploy.sh

echo "=== Deploying model to KServe ==="

# Получаем параметры
EXPERIMENT_NAME="cifar10-baseline"
MODEL_NAME="cifar10-cnn-baseline"
RUN_ID=$(cat /tmp/run_id.txt)

echo "Run ID: $RUN_ID"
echo "Model Name: $MODEL_NAME"

# Получаем URI модели из MLflow
MLFLOW_URL="http://mlflow-server.mlflow-system.svc.cluster.local:5000"
MODEL_URI="s3://mlflow/0/${RUN_ID}/artifacts/model"

# Создаем InferenceService манифест
cat > /tmp/inferenceservice.yaml << EOF
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: cifar10-cnn-baseline
  namespace: kserve
  annotations:
    serving.kserve.io/s3-endpoint: minio.mlflow-system.svc.cluster.local:9000
    serving.kserve.io/s3-usehttps: "0"
spec:
  predictor:
    serviceAccountName: default
    tensorflow:
      storageUri: "${MODEL_URI}"
      env:
      - name: AWS_ACCESS_KEY_ID
        valueFrom:
          secretKeyRef:
            name: minio-secret
            key: AWS_ACCESS_KEY_ID
      - name: AWS_SECRET_ACCESS_KEY
        valueFrom:
          secretKeyRef:
            name: minio-secret
            key: AWS_SECRET_ACCESS_KEY
EOF

echo "Applying InferenceService..."
kubectl apply -f /tmp/inferenceservice.yaml

echo "Waiting for model to be ready..."
kubectl wait --for=condition=ready inferenceservice cifar10-cnn-baseline -n kserve --timeout=300s

echo "=== Deployment completed ==="
echo "Model deployed as InferenceService: cifar10-cnn-baseline"
4. Создаем секрет для MinIO (если еще не создан):
bash
# Создаем секрет с учетными данными MinIO для KServe
kubectl create secret generic minio-secret \
  --from-literal=AWS_ACCESS_KEY_ID=minioadmin \
  --from-literal=AWS_SECRET_ACCESS_KEY=minioadmin \
  -n kserve
5. Собираем образы:
bash
# Переключаемся на docker daemon Minikube
eval $(minikube docker-env)

# Собираем образ для обучения
cd ~/mlops-infra
docker build -t mlops-train:latest -f docker/train/Dockerfile docker/train/

# Собираем образ для деплоя
docker build -t mlops-deploy:latest -f docker/deploy/Dockerfile docker/deploy/
6. Создаем пайплайн KFP:
python
# ~/mlops-infra/pipelines/cifar10_baseline.py
import kfp
from kfp import dsl
from kfp.components import create_component_from_func
from typing import NamedTuple

# 1. Компонент для загрузки данных
def load_data() -> NamedTuple('Outputs', [('data_loaded', str)]):
    import tensorflow as tf
    
    print("Loading CIFAR-10 dataset...")
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    
    print(f"Training data shape: {x_train.shape}")
    print(f"Test data shape: {x_test.shape}")
    
    from collections import namedtuple
    outputs = namedtuple('Outputs', ['data_loaded'])
    return outputs('success')

load_data_op = create_component_from_func(
    load_data,
    base_image='tensorflow/tensorflow:2.13.0',
    output_component_file='components/load_data.yaml'
)

# 2. Компонент для обучения
def train_model(epochs: int = 5) -> NamedTuple('Outputs', [('run_id', str), ('accuracy', float)]):
    import mlflow
    import tensorflow as tf
    import numpy as np
    import json
    
    mlflow.set_tracking_uri("http://mlflow-server.mlflow-system.svc.cluster.local:5000")
    mlflow.set_experiment("cifar10-baseline")
    
    # Загрузка данных
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    y_train = tf.keras.utils.to_categorical(y_train, 10)
    y_test = tf.keras.utils.to_categorical(y_test, 10)
    
    # Создание модели
    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(10, activation='softmax')
    ])
    
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    # Обучение с логированием в MLflow
    with mlflow.start_run() as run:
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("dataset", "CIFAR-10")
        
        history = model.fit(x_train, y_train,
                          epochs=epochs,
                          batch_size=64,
                          validation_split=0.2,
                          verbose=1)
        
        test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=0)
        mlflow.log_metric("test_accuracy", test_accuracy)
        mlflow.log_metric("test_loss", test_loss)
        
        # Сохранение модели
        mlflow.tensorflow.log_model(model, "model",
                                   registered_model_name="cifar10-cnn-baseline")
        
        # Сохраняем run_id в файл для следующего компонента
        with open('/tmp/run_id.txt', 'w') as f:
            f.write(run.info.run_id)
        
        from collections import namedtuple
        outputs = namedtuple('Outputs', ['run_id', 'accuracy'])
        return outputs(run.info.run_id, float(test_accuracy))

train_model_op = create_component_from_func(
    train_model,
    packages_to_install=['mlflow==2.9.0', 'tensorflow==2.13.0'],
    base_image='python:3.9',
    output_component_file='components/train_model.yaml'
)

# 3. Компонент для деплоя
def deploy_model(run_id: str) -> str:
    import subprocess
    import yaml
    
    # Создаем манифест InferenceService
    model_uri = f"s3://mlflow/0/{run_id}/artifacts/model"
    
    manifest = {
        'apiVersion': 'serving.kserve.io/v1beta1',
        'kind': 'InferenceService',
        'metadata': {
            'name': 'cifar10-cnn-baseline',
            'namespace': 'kserve',
            'annotations': {
                'serving.kserve.io/s3-endpoint': 'minio.mlflow-system.svc.cluster.local:9000',
                'serving.kserve.io/s3-usehttps': '0'
            }
        },
        'spec': {
            'predictor': {
                'serviceAccountName': 'default',
                'tensorflow': {
                    'storageUri': model_uri,
                    'env': [
                        {
                            'name': 'AWS_ACCESS_KEY_ID',
                            'valueFrom': {
                                'secretKeyRef': {
                                    'name': 'minio-secret',
                                    'key': 'AWS_ACCESS_KEY_ID'
                                }
                            }
                        },
                        {
                            'name': 'AWS_SECRET_ACCESS_KEY',
                            'valueFrom': {
                                'secretKeyRef': {
                                    'name': 'minio-secret',
                                    'key': 'AWS_SECRET_ACCESS_KEY'
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    
    # Применяем манифест
    with open('/tmp/inferenceservice.yaml', 'w') as f:
        yaml.dump(manifest, f)
    
    result = subprocess.run(['kubectl', 'apply', '-f', '/tmp/inferenceservice.yaml'],
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        return f"Model deployed successfully: {model_uri}"
    else:
        return f"Deployment failed: {result.stderr}"

deploy_model_op = create_component_from_func(
    deploy_model,
    base_image='bitnami/kubectl:latest',
    output_component_file='components/deploy_model.yaml'
)

# 4. Определяем пайплайн
@dsl.pipeline(
    name='CIFAR-10 Baseline Pipeline',
    description='Baseline CNN training on CIFAR-10 with MLflow logging and KServe deployment'
)
def cifar10_baseline_pipeline(epochs: int = 5):
    # Шаг 1: Загрузка данных
    load_data_task = load_data_op()
    
    # Шаг 2: Обучение модели
    train_task = train_model_op(epochs=epochs)
    train_task.after(load_data_task)
    
    # Шаг 3: Деплой модели
    deploy_task = deploy_model_op(run_id=train_task.outputs['run_id'])
    deploy_task.after(train_task)

# 5. Компилируем пайплайн
if __name__ == '__main__':
    from kfp.compiler import Compiler
    
    Compiler().compile(
        pipeline_func=cifar10_baseline_pipeline,
        package_path='cifar10_baseline_pipeline.yaml'
    )
    print("Pipeline compiled successfully!")
7. Компилируем и запускаем пайплайн:
bash
# Создаем директории
mkdir -p ~/mlops-infra/pipelines/components

# Устанавливаем KFP SDK если нужно
pip install kfp==2.0.0b11 kfp-pipeline-spec==0.2.2

# Компилируем пайплайн
cd ~/mlops-infra/pipelines
python cifar10_baseline.py

# Запускаем пайплайн через KFP API
KFP_HOST="http://localhost:8888"  # Если есть port-forward для KFP API

# Или через UI KFP (если доступен)
echo "Pipeline compiled: cifar10_baseline_pipeline.yaml"
echo "Upload this file to KFP UI at http://localhost:8081"
8. Упрощенный вариант пайплайна (без компиляции):
Создайте простой пайплайн для быстрого тестирования:

bash
# ~/mlops-infra/scripts/run-baseline.sh
#!/bin/bash

echo "=== Running CIFAR-10 Baseline Pipeline ==="

# 1. Создаем PVC для данных если нужно
kubectl apply -f - << EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cifar10-data-pvc
  namespace: kubeflow-pipelines
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# 2. Запускаем Job для обучения
kubectl apply -f - << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: cifar10-train-job
  namespace: kubeflow-pipelines
spec:
  template:
    spec:
      containers:
      - name: train
        image: mlops-train:latest
        env:
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow-server.mlflow-system.svc.cluster.local:5000"
        volumeMounts:
        - name: data
          mountPath: /tmp
      restartPolicy: Never
      volumes:
      - name: data
        emptyDir: {}
EOF

# 3. Ждем завершения обучения
echo "Waiting for training to complete..."
kubectl wait --for=condition=complete job/cifar10-train-job -n kubeflow-pipelines --timeout=600s

# 4. Копируем run_id
kubectl logs -n kubeflow-pipelines job/cifar10-train-job | grep "MLflow Run ID:" | cut -d' ' -f4 > /tmp/run_id.txt
RUN_ID=$(cat /tmp/run_id.txt)
echo "Run ID: $RUN_ID"

# 5. Запускаем деплой
kubectl apply -f - << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: cifar10-deploy-job
  namespace: kubeflow-pipelines
spec:
  template:
    spec:
      containers:
      - name: deploy
        image: mlops-deploy:latest
        env:
        - name: RUN_ID
          value: "$RUN_ID"
        volumeMounts:
        - name: run-id
          mountPath: /tmp
      restartPolicy: Never
      volumes:
      - name: run-id
        configMap:
          name: run-id-config
EOF

echo "=== Baseline pipeline started ==="
echo "Check training logs: kubectl logs -n kubeflow-pipelines job/cifar10-train-job"
echo "Check deployment: kubectl get inferenceservice -n kserve"
9. Проверяем работу модели:
bash
# Проверяем InferenceService
kubectl get inferenceservice cifar10-cnn-baseline -n kserve

# Тестируем модель
cat > ~/mlops-infra/scripts/test-model.sh << 'EOF'
#!/bin/bash

echo "=== Testing CIFAR-10 Model ==="

# Создаем тестовый запрос
cat > /tmp/test_request.json << 'EOJ'
{
  "instances": [
    [[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]], 
     [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],
     [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]]
  ]
}
EOJ

# Отправляем запрос
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Host: cifar10-cnn-baseline.kserve.example.com" \
  http://localhost:8080/v1/models/cifar10-cnn-baseline:predict \
  -d @/tmp/test_request.json

echo ""
echo "=== Test completed ==="
EOF

chmod +x ~/mlops-infra/scripts/test-model.sh
10. Создаем README для Baseline конфигурации:
bash
cat > ~/mlops-infra/BASELINE-README.md << 'EOF'
# Конфигурация 1: Baseline (без защиты)

## Описание
Базовая конфигурация для обучения CNN на CIFAR-10 без каких-либо механизмов безопасности.

## Компоненты
1. **Kubeflow Pipelines** - оркестрация пайплайна
2. **MLflow** - трекинг экспериментов и моделей
3. **KServe** - serving модели
4. **MinIO** - хранение артефактов

## Пайплайн
1. **Загрузка данных** - CIFAR-10 dataset
2. **Обучение модели** - CNN архитектура
3. **Логирование в MLflow** - параметры, метрики, модель
4. **Деплой в KServe** - создание InferenceService

## Запуск

### Вариант 1: Полный пайплайн KFP
```bash
cd ~/mlops-infra/pipelines
python cifar10_baseline.py
# Загрузите cifar10_baseline_pipeline.yaml в KFP UI
Вариант 2: Упрощенный запуск
bash
./scripts/run-baseline.sh
Вариант 3: Вручную
bash
# 1. Обучить модель
kubectl apply -f k8s/jobs/train-job.yaml

# 2. Деплой модели
kubectl apply -f k8s/istio-kserve/cifar10-inferenceservice.yaml
Проверка
MLflow UI: http://localhost:5000

Эксперимент: cifar10-baseline

Модель: cifar10-cnn-baseline

KServe:

bash
kubectl get inferenceservice -n kserve
curl -H "Host: cifar10-cnn-baseline.kserve.example.com" \
  http://localhost:8080/v1/models/cifar10-cnn-baseline:predict \
  -d '{"instances": [...]}'
Модель
Архитектура: CNN (3 слоя Conv2D + 2 Dense)

Данные: CIFAR-10 (32x32 RGB изображения, 10 классов)

Метрики: Accuracy, Loss

Формат: TensorFlow SavedModel

Хранение
Модель: MinIO (s3://mlflow/<run_id>/artifacts/model)

Метаданные: PostgreSQL MLflow

Логи: MLflow Tracking Server

Примечания
Это базовая конфигурация без:

Проверки качества модели

Валидации данных

Мониторинга дрифта

Безопасности доступа

Шифрования данных
EOF

text

## Итог:

Вы создали "Конфигурацию 1" (Baseline) которая включает:

1. **Датасет**: CIFAR-10
2. **Пайплайн обучения**: CNN в KFP без гейтов
3. **Логирование**: Полное логирование в MLflow
4. **Деплой**: KServe InferenceService

Теперь у вас есть точка отсчета для сравнения с защищенными конфигурациями!


на 7 пункте