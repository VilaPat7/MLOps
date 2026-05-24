#!/bin/bash

echo "=== MLOps Infrastructure Check ==="
echo ""

echo "1. Minikube:"
if minikube status | grep -q "Running"; then
    echo "   ✅ Minikube is running"
else
    echo "   ❌ Minikube is not running"
    echo "   Starting Minikube..."
    minikube start --memory=12288 --cpus=6 --addons=ingress --cni=bridge
fi
echo ""

echo "3. MLflow:"
MLFLOW_PODS=$(kubectl get pods -n mlflow-system 2>/dev/null | grep -c "Running")
if [ "$MLFLOW_PODS" -ge 3 ]; then
    echo "   ✅ MLflow is running ($MLFLOW_PODS pods)"
else
    echo "   ❌ MLflow is not running ($MLFLOW_PODS pods)"
    echo "   Starting MLflow..."
    kubectl apply -f ~/mlops-infra/k8s/mlflow/namespace.yaml 2>/dev/null
    kubectl apply -f ~/mlops-infra/k8s/mlflow/postgresql.yaml 2>/dev/null
    kubectl apply -f ~/mlops-infra/k8s/mlflow/minio.yaml 2>/dev/null
    kubectl apply -f ~/mlops-infra/k8s/mlflow/mlflow-server.yaml 2>/dev/null
    echo "   Waiting for MLflow pods to start..."
    sleep 15
fi
echo ""

echo "4. Istio:"
ISTIO_PODS=$(kubectl get pods -n istio-system 2>/dev/null | grep -c "Running")
if [ "$ISTIO_PODS" -ge 1 ]; then
    echo "   ✅ Istio is running ($ISTIO_PODS pods)"
else
    echo "   ❌ Istio is not running"
    echo "   Starting Istio and KServe..."
    if [ -f ~/mlops-infra/scripts/install-istio-kserve.sh ]; then
        chmod +x ~/mlops-infra/scripts/install-istio-kserve.sh
        ~/mlops-infra/scripts/install-istio-kserve.sh
    else
        echo "   Istio installation script not found"
    fi
fi
echo ""

echo "5. TensorFlow Serving:"
if kubectl get deployment cifar10-tf-serving -n default &>/dev/null; then
    READY=$(kubectl get deployment cifar10-tf-serving -n default -o jsonpath='{.status.readyReplicas}')
    if [ "$READY" -ge 1 ]; then
        echo "   ✅ TensorFlow Serving is running (replicas: $READY)"
    else
        echo "   ❌ TensorFlow Serving is not ready"
    fi
else
    echo "   ⚠️  TensorFlow Serving not deployed. Run: kubectl apply -f tf-serving-deployment.yaml"
fi
echo ""

echo "=== Final Status ==="
echo "All namespaces:"
kubectl get namespaces | grep -E "kubeflow|mlflow|istio"
echo ""
echo "All pods:"
kubectl get pods -A | grep -E "kubeflow|mlflow|istio"
echo ""
echo "=== Check completed ==="
echo ""
echo "To open access to UI, run: ./scripts/access-all.sh"
echo "To stop everything, run: ./scripts/stop-all.sh"
