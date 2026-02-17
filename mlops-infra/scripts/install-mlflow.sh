#!/bin/bash
set -e

echo "=== Installing MLflow Server ==="

# 1. Create namespace
echo "Creating namespace mlflow-system..."
kubectl create namespace mlflow-system --dry-run=client -o yaml | kubectl apply -f -

# 2. Create directories in Minikube
echo "Creating directories for MLflow..."
minikube ssh "sudo mkdir -p /data/mlflow-postgres /data/mlflow-minio && sudo chmod 777 /data/mlflow-postgres /data/mlflow-minio"

# 3. Install PostgreSQL
echo "Installing PostgreSQL..."
cat <<'PGEOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mlflow-postgres-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /data/mlflow-postgres
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mlflow-postgres-pvc
  namespace: mlflow-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  namespace: mlflow-system
spec:
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: mlflow
        - name: POSTGRES_USER
          value: mlflowuser
        - name: POSTGRES_PASSWORD
          value: mlflowpass
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: mlflow-postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: mlflow-system
spec:
  ports:
  - port: 5432
  selector:
    app: postgresql
PGEOF

# 4. Install MinIO
echo "Installing MinIO for artifacts..."
cat <<'MINIOEOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mlflow-minio-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /data/mlflow-minio
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mlflow-minio-pvc
  namespace: mlflow-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: mlflow-system
spec:
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio
        args:
        - server
        - /data
        env:
        - name: MINIO_ROOT_USER
          value: "mlflowminio"
        - name: MINIO_ROOT_PASSWORD
          value: "mlflowminio123"
        ports:
        - containerPort: 9000
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: mlflow-minio-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: mlflow-system
spec:
  ports:
  - port: 9000
    targetPort: 9000
  selector:
    app: minio
MINIOEOF

# 5. Install MLflow Tracking Server
echo "Installing MLflow Tracking Server..."
cat <<'MLFLOWEOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
  namespace: mlflow-system
spec:
  selector:
    matchLabels:
      app: mlflow-server
  template:
    metadata:
      labels:
        app: mlflow-server
    spec:
      containers:
      - name: mlflow-server
        image: ghcr.io/mlflow/mlflow:latest
        ports:
        - containerPort: 5000
        env:
        - name: MLFLOW_S3_ENDPOINT_URL
          value: "http://minio:9000"
        - name: AWS_ACCESS_KEY_ID
          value: "mlflowminio"
        - name: AWS_SECRET_ACCESS_KEY
          value: "mlflowminio123"
        command: ["mlflow", "server"]
        args:
          - "--host=0.0.0.0"
          - "--port=5000"
          - "--backend-store-uri=postgresql://mlflowuser:mlflowpass@postgresql:5432/mlflow"
          - "--default-artifact-root=s3://mlflow"
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-server
  namespace: mlflow-system
spec:
  ports:
  - port: 5000
    targetPort: 5000
  selector:
    app: mlflow-server
MLFLOWEOF

# 6. Wait for startup
echo "Waiting for components to start (120 seconds)..."
sleep 120

# 7. Verify installation
echo "=== MLflow Installation Verification ==="
kubectl get pods -n mlflow-system
kubectl get svc -n mlflow-system

echo ""
echo "=== MLflow Access ==="
echo "MLflow UI: kubectl port-forward -n mlflow-system svc/mlflow-server 5000:5000"
echo "Then open: http://localhost:5000"
