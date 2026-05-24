#!/bin/bash
set -e

echo "=== MLOps Platform Deployment ==="

command -v minikube >/dev/null 2>&1 || { echo "Minikube not found. Please install."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "Helm not found. Please install."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Kubectl not found. Please install."; exit 1; }

if ! minikube status | grep -q "Running"; then
    echo "Starting Minikube..."
    minikube start --cpus=6 --memory=12288 --addons=ingress --cni=bridge
else
    echo "Minikube is already running."
fi

echo "Building Docker images in Minikube..."
make minikube-build

echo "Deploying Helm chart..."
make helm-upgrade

echo "Checking pods..."
kubectl get pods -A

echo "Deployment completed successfully!"
