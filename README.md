# MLOps with Security Gates for CIFAR-10

This project implements a secure machine learning pipeline for the CIFAR-10 dataset. The system is deployed on Kubernetes (Minikube/kind) and includes:

- **Kubeflow Pipelines (KFP)** – orchestration of training with conditional logic.
- **MLflow** – experiment tracking and model registry (with MinIO and PostgreSQL).
- **TensorFlow Serving** – model deployment in production.
- **Istio** – authentication (JWT) and authorization policies.
- **5 Security Gates**:
  1. `gate1_data_validation` – label distribution check (Data Poisoning).
  2. `gate2` – built into training: Differential Privacy (TensorFlow Privacy).
  3. `gate3_model_validation` – model metric validation (accuracy/loss).
  4. `gate4_signature_verify` – digital signing and verification of the model.
  5. `gate5_inference_preprocess` – input validation and anomaly detection (autoencoder).

Two deployment configurations are supported:
- **Baseline** – unprotected inference (plain TF Serving).
- **Protected** – full protection (all gates + Istio JWT).

## Repository Structure
```
├── Makefile # Build, push images, deploy
├── deploy.sh # Quick platform deployment
├── destroy.sh # Remove all resources
│
├── baseline/ # Baseline configuration (no gates)
│ └── train-job.yaml # Kubernetes Job for baseline model training
│
├── configs/ # Environment configurations
│ └── values-prod.yaml # Production values for Helm
│
├── docker/ # Dockerfiles for all components
│ ├── gates/ # Gate containers for KFP
│ │ ├── gate1_data_validation/ # Data validation
│ │ ├── gate3_model_validation/ # Model validation
│ │ ├── gate4_signature_verify/ # Signing and verification
│ │ ├── gate5_inference_preprocess/ # Preprocessing + anomaly detector
│ │ └── register_model/ # Register model in MLflow
│ ├── inference/ # Custom preprocessor for inference
│ │ └── preprocessor/ # FastAPI server with Gate5 (preprocess + anomaly detector)
│ └── train/ # Training component (integrates Gate2 DP)
│
├── experiments/ # Attack scripts and experiments
│ ├── poison.py # Data poisoning (ML02)
│ ├── gen_adv.py # Adversarial example generation (ML01)
│ ├── mia_attack.py # Membership inference attack (ML04)
│ ├── train_dp.py # Training with Differential Privacy
│ ├── train_simple.py # Plain training
│ ├── test_adv_*.py # Adversarial attack testing
│ └── *.log, *.pkl, *.h5 # Experiment artifacts
│
├── helm/ # Helm charts for the platform
│ └── mlops-platform/
│ ├── Chart.yaml
│ ├── values.yaml
│ └── templates/ # All K8s manifests (MLflow, MinIO, PostgreSQL,
│ # baseline-deployment, protected-deployment,
│ # HPA, Istio policies, secrets, etc.)
│
├── istio/ # Standalone Istio policies
│ ├── auth-policy.yaml # AuthorizationPolicy
│ └── request-auth.yaml # RequestAuthentication (JWT)
│
├── k8s/ # Manual manifests (components not in Helm)
│ ├── inference/ # Inference service deployment (Deployment, HPA, Service)
│ ├── kfp/ # Kubeflow Pipelines installation (namespace, components)
│ │ ├── components/ # KFP components: gate1, gate3, gate4, register, train, train_dp
│ │ ├── kfp-minimal.yaml
│ │ └── kfp-full.yaml
│ ├── mlflow/ # MLflow, MinIO, PostgreSQL (namespace, server, deployments)
│ └── tf-serving/ # TensorFlow Serving (model loader job, pvc, deployment, service)
│
├── pipelines/ # KFP pipeline
│ └── secure_training_pipeline.py # Secure pipeline definition with conditions
│
└── scripts/ # Helper scripts
├── deploy.sh # Deploy the whole platform
├── deploy-kfp.sh # Deploy KFP
├── install-mlflow.sh # Install MLflow
├── install-istio-kserve.sh # Install Istio + KServe
├── build_push_gates.sh # Build and push gate images
├── generate_keys.sh # Generate keys for model signing
├── run-baseline.sh # Run baseline pipeline
├── quick-status.sh # Status of all pods
├── stop-all.sh # Stop all components
└── keys/ # Private and public keys for signing
```
## Prerequisites

- **Kubernetes** (Minikube or kind) + `kubectl`
- **Helm** 3.x
- **Docker** (or Podman)
- **Python** 3.10+ (locally for running KFP pipelines)
- **KFP SDK**: `pip install kfp`

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/VilaPat7/MLOps.git

cd MLOps
```
### 2. Build and publish Docker images
```bash
make build-images   # builds all images (gates, train, preprocessor)
make push-images    # pushes to your registry (set REGISTRY in Makefile)
```
### 3. Deploy the platform
```bash
./deploy.sh
```
This will:

- Install Istio, KFP, MLflow (with MinIO and PostgreSQL), TensorFlow Serving.

- Create namespaces (kubeflow, mlflow, inference).

- Apply the Helm chart mlops-platform with configuration from configs/values-prod.yaml.

Check pods:

```bash
kubectl get pods -A | grep -E 'kubeflow|mlflow|inference|istio'
```
### 4. Run the secure training pipeline
The pipeline is defined in pipelines/secure_training_pipeline.py. It sequentially executes:

- Gate1 – data validation (check label distribution of CIFAR-10).

- Training (optionally includes Gate2 – Differential Privacy via the train_dp component).

- Gate3 – model quality check (accuracy > threshold).

- Gate4 – sign the model with a private key.

- Register the model in MLflow (save as SavedModel).

Run via KFP SDK:

```bash
python pipelines/secure_training_pipeline.py
```
Or upload the pipeline to the KFP web interface.

### 5. Deploy secure inference
To deploy the protected version (with Gate4, Gate5 and Istio JWT):

```bash
helm upgrade --install inference ./helm/mlops-platform \
  --set inference.type=protected \
  --values configs/values-prod.yaml
  ```
For the baseline version (plain TF Serving without checks):

```bash
helm upgrade --install inference ./helm/mlops-platform \
  --set inference.type=baseline
  ```
After deployment, the service is available via the Istio Ingress.
Example request with JWT token:

```bash
export TOKEN=$(python scripts/generate_jwt.py)   # or use generate_keys.sh
curl -X POST https://inference.local/v1/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @docker/inference/preprocessor/req.json
  ```
## Security Components
| Gate | Implementation | Where it is used |
| --- | --- | --- |
| Gate1 – Data Poisoning | `gate1_data_validation/validate_data.py` (statistical test) | KFP component before training |
| Gate2 – Differential Privacy | Built into `docker/train/train.py` (TensorFlow Privacy) | Optional in the pipeline |
| Gate3 – Model Integrity | `gate3_model_validation/validate_model.py` (accuracy check) | After training |
| Gate4 – Model Provenance | `gate4_signature_verify/sign_model.py` + `verify_signature.py` | Signing after Gate3, verification at inference load |
| Gate5 – Input Validation & Adversarial Detection | `gate5_inference_preprocess/preprocess.py` (Pydantic + autoencoder) | Called in the inference preprocessor (`docker/inference/preprocessor`) |
| Gate6 – Authentication & Rate Limiting | Istio `RequestAuthentication` + `AuthorizationPolicy` (JWT) | On the ingress gateway to the inference service |


## Attack Experiments
The experiments/ folder contains scripts to test the effectiveness of the gates:

1. **Data Poisoning** (poison.py) – creates a poisoned dataset. The baseline model accuracy drops, while the protected pipeline stops at Gate1.

2. **Adversarial Attack** (gen_adv.py, test_adv_*.py) – generates adversarial examples (PGD). Baseline is vulnerable, protected rejects >85% of requests via Gate5.

3. **Membership Inference** (mia_attack.py, simulate_dp_mia.py) – shows that the model with Gate2 (DP) is robust to MIA (AUC ~0.5).

4. **Load testing** – run experiments/test_adv_protected.py with high request rate to test rate limiting (configured in Istio).

Example attack run:

```bash
cd experiments
python poison.py --dataset cifar10 --poison_rate 0.3
python test_adv_baseline.py  # compares baseline and protected
```
## Comparison Results
| Configuration | Data Poisoning | Adversarial | Membership Inference | Latency p99 |
| --- | --- | --- | --- | --- |
| Baseline | Accuracy drops by 40% | 92% successful attacks | AUC 0.81 | 25 ms |
| Protected (without Gate2) | Stops at Gate1 | 89% rejected | AUC 0.77 | 95 ms |
| Protected (with Gate2, ε=3) | Stops at Gate1 | 91% rejected | AUC 0.52 | 98 ms |

**Training time**: Protected pipeline is 35% slower than Baseline due to the checks.
**Accuracy/Privacy trade-off**: with ε=1 model accuracy drops to 76% (was 83%).

## Management
1. **Stop all services**: `./stop-all.sh`

2. **Full removal**: `./destroy.sh` (caution – deletes all namespaces)

3. **Status**: `./scripts/quick-status.sh`

## Known Limitations
1. Supports only CIFAR-10 (other datasets require modifying Gate1 and the anomaly detector).

2. Gate2 (Differential Privacy) is implemented only for TensorFlow 2.x (TF Privacy).

3. The autoencoder for Gate5 needs periodic retraining on new data.

