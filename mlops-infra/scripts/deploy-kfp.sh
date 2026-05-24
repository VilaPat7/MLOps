#!/bin/bash
set -e

echo "=== Installing Kubeflow Pipelines ==="

echo "Creating namespace for Kubeflow Pipelines..."
kubectl apply -f ../k8s/kfp/namespace.yaml

echo "Creating directory for artifacts in Minikube..."
minikube ssh "sudo mkdir -p /data/kfp-artifacts && sudo chmod 777 /data/kfp-artifacts"

echo "Installing Persistent Volume and MinIO..."
kubectl apply -f ../k8s/storage/kfp-storage.yaml

echo "Installing Kubeflow Pipelines..."
kubectl apply -f ../k8s/kfp/kfp-full.yaml

echo "Waiting for components to start (60 seconds)..."
sleep 60

echo "=== Verifying KFP Installation ==="
kubectl get pods -n kubeflow-pipelines
kubectl get svc -n kubeflow-pipelines

echo ""
echo "=== Access Instructions ==="
echo "1. KFP UI: kubectl port-forward -n kubeflow-pipelines svc/ml-pipeline-ui 8080:80"
echo "   Then open: http://localhost:8080"
echo ""
echo "2. MinIO Console: kubectl port-forward -n kubeflow-pipelines svc/minio 9001:9001"
echo "   Then open: http://localhost:9001"
echo "   Login: minioadmin, Password: minioadmin123"
