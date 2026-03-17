#!/bin/bash
set -e

echo "=== MLOps Platform Deployment ==="

# Проверка необходимых инструментов
command -v minikube >/dev/null 2>&1 || { echo "Minikube not found. Please install."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "Helm not found. Please install."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Kubectl not found. Please install."; exit 1; }

# Запуск Minikube если не запущен
if ! minikube status | grep -q "Running"; then
    echo "Starting Minikube..."
    minikube start --cpus=6 --memory=12288 --addons=ingress --cni=bridge
else
    echo "Minikube is already running."
fi

# Сборка образов в Minikube (если нужно использовать локальные)
echo "Building Docker images in Minikube..."
make minikube-build

# Установка/обновление Helm-чарта
echo "Deploying Helm chart..."
make helm-upgrade

# Проверка статуса подов
echo "Checking pods..."
kubectl get pods -A

# Установка мониторинга (Prometheus + Grafana)
echo "Installing monitoring stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace --wait

echo "Deployment completed successfully!"
