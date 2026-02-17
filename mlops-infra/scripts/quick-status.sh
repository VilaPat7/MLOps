#!/bin/bash

echo "=== Quick Status Check ==="
echo ""

echo "1. Minikube:"
minikube status | head -3
echo ""

echo "2. Namespaces:"
kubectl get namespaces | grep -E "kubeflow|mlflow|istio|kserve|monitoring"
echo ""

echo "3. Pods by namespace:"
for ns in kubeflow-pipelines mlflow-system istio-system kserve kserve-system monitoring; do
    echo "   $ns:"
    kubectl get pods -n $ns 2>/dev/null | awk 'NR<=3 {print "      "$0}'
    if [ $? -ne 0 ]; then
        echo "      (namespace not found or no pods)"
    fi
    echo ""
done

echo "4. Services exposed:"
echo "   MLflow UI:        $(kubectl get svc mlflow-server -n mlflow-system 2>/dev/null | grep -q . && echo 'Ready' || echo 'Not found')"
echo "   Grafana:          $(kubectl get svc grafana -n monitoring 2>/dev/null | grep -q . && echo 'Ready' || echo 'Not found')"
echo "   Prometheus:       $(kubectl get svc prometheus -n monitoring 2>/dev/null | grep -q . && echo 'Ready' || echo 'Not found')"
echo "   KFP UI:           $(kubectl get svc ml-pipeline-ui -n kubeflow-pipelines 2>/dev/null | grep -q . && echo 'Ready' || echo 'Not found')"
echo "   Istio Ingress:    $(kubectl get svc istio-ingressgateway -n istio-system 2>/dev/null | grep -q . && echo 'Ready' || echo 'Not found')"
echo ""

echo "=== Quick check completed ==="
