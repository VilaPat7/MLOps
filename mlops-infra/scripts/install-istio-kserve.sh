echo "=== Installing Istio ==="

# Install Istio CLI
if ! command -v istioctl &> /dev/null; then
    echo "Downloading Istio..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.19.0 sh -
    cd istio-1.19.0
    export PATH=$PWD/bin:$PATH
    cd ..
else
    echo "Istio CLI is already installed"
fi

# Install Istio into the cluster
kubectl create namespace istio-system
istioctl install --set profile=demo -y

# Enable sidecar injection for the kserve namespace
kubectl create namespace kserve
kubectl label namespace kserve istio-injection=enabled

echo "=== Installing KServe ==="

# Install KServe
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.13.0/kserve.yaml

# Wait for the KServe Controller to be ready
echo "Waiting for KServe Controller to be ready..."
kubectl wait --for=condition=ready pod -l control-plane=kserve-controller-manager -n kserve-system --timeout=300s

echo "=== Configuring Network ==="

# Create Gateway and VirtualService for KServe
cat <<EOL | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: kserve-gateway
  namespace: kserve
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: kserve-vs
  namespace: kserve
spec:
  hosts:
  - "*"
  gateways:
  - kserve-gateway
  http:
  - match:
    - uri:
        prefix: /v1/models/
    route:
    - destination:
        host: kserve.kserve.kserve-system.svc.cluster.local
        port:
          number: 80
EOL

echo "=== Installation completed ==="
echo "Check status:"
echo "kubectl get pods -n istio-system"
echo "kubectl get pods -n kserve-system"
