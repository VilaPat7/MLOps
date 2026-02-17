#!/bin/bash

echo "=== Deploying model to KServe ==="

EXPERIMENT_NAME="cifar10-baseline"
MODEL_NAME="cifar10-cnn-baseline"
RUN_ID=$(cat /tmp/run_id.txt)

echo "Run ID: $RUN_ID"
echo "Model Name: $MODEL_NAME"

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
