#!/bin/bash
# run-baseline.sh - Полный пайплайн для CIFAR-10 baseline с ручным вводом URI модели

set -e  # остановка при ошибке

echo "=== Starting baseline pipeline for CIFAR-10 ==="

# 1. Запуск обучения
echo "Submitting training job..."
kubectl apply -f ~/mlops-infra/baseline/train-job.yaml

echo "Waiting for training job to complete..."
kubectl wait --for=condition=complete job/cifar10-train-job -n default --timeout=600s

# 2. Получение URI модели
# Если передан аргумент, используем его, иначе запрашиваем ввод
if [ -n "$1" ]; then
    MODEL_URI="$1"
    echo "Using provided URI: $MODEL_URI"
else
    echo ""
    echo "Please enter the model URI from MLflow (e.g., s3://mlflow/1/xxxx/artifacts/model/):"
    read -p "URI: " MODEL_URI
    if [ -z "$MODEL_URI" ]; then
        echo "No URI provided. Exiting."
        exit 1
    fi
fi

# 3. Создание PVC, если не существует
if ! kubectl get pvc model-pvc -n default &>/dev/null; then
    echo "Creating PVC..."
    kubectl apply -f ~/mlops-infra/k8s/tf-serving/model-pvc.yaml
    sleep 5
fi

# 4. Запуск Job для загрузки модели в PVC
echo "Running model loader job..."
kubectl delete job model-loader -n default --ignore-not-found
# Подставляем URI в job (через sed)
sed "s|REPLACE_MODEL_URI|$MODEL_URI|g" ~/mlops-infra/k8s/tf-serving/model-loader-job.yaml | kubectl apply -f -

echo "Waiting for model loader job to complete..."
kubectl wait --for=condition=complete job/model-loader -n default --timeout=300s

# 5. Деплой TensorFlow Serving
echo "Deploying TensorFlow Serving..."
kubectl apply -f ~/mlops-infra/k8s/tf-serving/tf-serving-deployment.yaml
kubectl apply -f ~/mlops-infra/k8s/tf-serving/tf-serving-service.yaml

echo "Waiting for serving pod to be ready..."
kubectl wait --for=condition=ready pod -l app=cifar10-tf-serving -n default --timeout=120s

# 6. Инструкция по тестированию
echo ""
echo "=== Baseline pipeline completed successfully ==="
echo ""
echo "Model is served at: cifar10-tf-serving.default.svc.cluster.local:8501"
echo ""
echo "To test locally, run:"
echo "  kubectl port-forward -n default svc/cifar10-tf-serving 8501:8501"
echo '  curl -d '"'"'{"instances": [[1.0, 2.0, 3.0, 4.0]]}'"'"' -H "Content-Type: application/json" -X POST http://localhost:8501/v1/models/cifar10:predict'
echo ""
