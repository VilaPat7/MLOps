#!/bin/bash
set -e

echo "=== MLOps Infrastructure Setup ==="

echo "Creating namespace for Kubeflow Pipelines..."
kubectl apply -f k8s/kfp/namespace.yaml

echo "Creating Persistent Volume..."
kubectl apply -f k8s/storage/kfp-pv.yaml

minikube ssh "sudo mkdir -p /data/kfp-artifacts && sudo chmod 777 /data/kfp-artifacts"

echo "Installing Kubeflow Pipelines..."
kubectl apply -f k8s/kfp/kfp-minimal.yaml

echo "Waiting for components to start..."
sleep 60

echo "=== Installation Verification ==="
kubectl get pods -n kubeflow-pipelines
kubectl get svc -n kubeflow-pipelines

echo "=== Service Access ==="
echo "KFP UI will be available at: http://localhost:8080"
echo "To access, run: kubectl port-forward -n kubeflow-pipelines svc/ml-pipeline-ui 8080:80"
