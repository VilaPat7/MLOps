#!/bin/bash

echo "=== Opening Access to MLOps Services ==="
echo ""

pkill -f "kubectl port-forward" 2>/dev/null
sleep 2

echo "1. MLflow UI: http://localhost:5000"
kubectl port-forward svc/mlflow-server 5000:5000 -n mlflow-system > /dev/null 2>&1 &
sleep 2

echo "2. MinIO Console (MLflow): http://localhost:9001"
kubectl port-forward svc/minio 9001:9001 -n mlflow-system > /dev/null 2>&1 &
sleep 2

echo "3. KFP MinIO Console: http://localhost:9002"
kubectl port-forward svc/minio 9002:9001 -n kubeflow-pipelines > /dev/null 2>&1 &
sleep 2

echo "4. TensorFlow Serving REST API: http://localhost:8501"
kubectl port-forward svc/cifar10-tf-serving 8501:8501 -n default > /dev/null 2>&1 &
sleep 2

echo "5. KFP UI (if available): http://localhost:8081"
kubectl port-forward svc/ml-pipeline-ui 8081:80 -n kubeflow-pipelines > /dev/null 2>&1 &
sleep 2

echo ""
echo "=== Services are now accessible ==="
echo ""
echo "To test functionality:"
echo "1. Open MLflow: http://localhost:5000"
echo "2. Check MinIO: http://localhost:9001 (login: minioadmin, password: minioadmin)"
echo "3. Test TensorFlow Serving:"
echo '   curl -d '\''{"instances": [[1.0, 2.0, 3.0, 4.0]]}'\'' -H "Content-Type: application/json" -X POST http://localhost:8501/v1/models/cifar10:predict'
echo ""
echo "To stop all port-forward processes:"
echo "pkill -f 'kubectl port-forward'"
echo ""
