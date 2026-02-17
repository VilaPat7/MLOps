#!/bin/bash
set -e

echo "=== Installing Kubeflow Pipelines ==="

# 1. Create namespace BEFORE everything else
echo "Creating namespace for Kubeflow Pipelines..."
kubectl apply -f ../k8s/kfp/namespace.yaml

# 2. Create directory in Minikube
echo "Creating directory for artifacts in Minikube..."
minikube ssh "sudo mkdir -p /data/kfp-artifacts && sudo chmod 777 /data/kfp-artifacts"

# 3. Install Persistent Volume and MinIO
echo "Installing Persistent Volume and MinIO..."
kubectl apply -f ../k8s/storage/kfp-storage.yaml

# 4. Install KFP
echo "Installing Kubeflow Pipelines..."
kubectl apply -f ../k8s/kfp/kfp-full.yaml

# 5. Wait for startup
echo "Waiting for components to start (60 seconds)..."
sleep 60

# 6. Verify installation
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
