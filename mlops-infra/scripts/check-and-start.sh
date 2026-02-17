#!/bin/bash

echo "=== MLOps Infrastructure Check ==="
echo ""

# 1. Minikube check
echo "1. Minikube:"
if minikube status | grep -q "Running"; then
    echo "   ✅ Minikube is running"
else
    echo "   ❌ Minikube is not running"
    echo "   Starting Minikube..."
    minikube start --memory=8192 --cpus=4 --addons=ingress
fi
echo ""

# 2. KFP check
echo "2. Kubeflow Pipelines:"
KFP_PODS=$(kubectl get pods -n kubeflow-pipelines 2>/dev/null | grep -c "Running")
if [ "$KFP_PODS" -ge 2 ]; then
    echo "   ✅ KFP is running ($KFP_PODS pods)"
else
    echo "   ❌ KFP is not running ($KFP_PODS pods)"
    echo "   Starting KFP..."
    kubectl apply -f ~/mlops-infra/k8s/kfp/namespace.yaml 2>/dev/null
    kubectl apply -f ~/mlops-infra/k8s/storage/kfp-storage.yaml 2>/dev/null
    kubectl apply -f ~/mlops-infra/k8s/kfp/kfp-minimal.yaml 2>/dev/null
    echo "   Waiting for KFP pods to start..."
    sleep 10
fi
echo ""

# 3. MLflow check
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

# 4. Istio check
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

# 5. KServe check
echo "5. KServe:"
if kubectl get pods -n kserve-system 2>/dev/null | grep -q "Running"; then
    echo "   ✅ KServe controller is running"
else
    echo "   ❌ KServe controller is not running"
    echo "   Install KServe: ./scripts/install-istio-kserve.sh"
fi

if kubectl get pods -n kserve 2>/dev/null | grep -q "Running"; then
    echo "   ✅ KServe models are running"
else
    echo "   ⚠️  No running models in KServe"
    echo "   To deploy test model: kubectl apply -f k8s/istio-kserve/example-inferenceservice.yaml"
fi
echo ""

# 6. Monitoring check
echo "6. Monitoring:"
MONITORING_PODS=$(kubectl get pods -n monitoring 2>/dev/null | grep -c "Running")
if [ "$MONITORING_PODS" -ge 2 ]; then
    echo "   ✅ Monitoring is running ($MONITORING_PODS pods)"
else
    echo "   ❌ Monitoring is not running ($MONITORING_PODS pods)"
    echo "   Starting Monitoring..."
    kubectl create namespace monitoring 2>/dev/null
    kubectl apply -f ~/mlops-infra/k8s/monitoring/prometheus.yaml 2>/dev/null
    kubectl apply -f ~/mlops-infra/k8s/monitoring/grafana.yaml 2>/dev/null
    echo "   Waiting for monitoring pods to start..."
    sleep 10
fi
echo ""

# 7. Final status
echo "=== Final Status ==="
echo "All namespaces:"
kubectl get namespaces | grep -E "kubeflow|mlflow|istio|kserve|monitoring"
echo ""
echo "All pods:"
kubectl get pods -A | grep -E "kubeflow|mlflow|istio|kserve|monitoring"
echo ""
echo "=== Check completed ==="
echo ""
echo "To open access to UI, run: ./scripts/access-all.sh"
echo "To stop everything, run: ./scripts/stop-all.sh"
