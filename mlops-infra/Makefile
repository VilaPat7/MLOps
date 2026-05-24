REGISTRY ?= docker.io/vika123vika
TAG ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")

.PHONY: all build-train build-gates build-inference push-all minikube-build

all: build-train build-gates build-inference

build-train:
	cd docker/train && DOCKER_BUILDKIT=0 docker build -t $(REGISTRY)/cifar10-train:$(TAG) .

build-gates: build-gate1 build-gate3 build-gate4 build-gate5 build-register

build-gate1:
	cd docker/gates/gate1_data_validation && DOCKER_BUILDKIT=0 docker build -t $(REGISTRY)/cifar10-gate1:$(TAG) .

build-gate3:
	cd docker/gates/gate3_model_validation && DOCKER_BUILDKIT=0 docker build -t $(REGISTRY)/cifar10-gate3:$(TAG) .

build-gate4:
	cd docker/gates/gate4_signature_verify && DOCKER_BUILDKIT=0 docker build -t $(REGISTRY)/cifar10-gate4:$(TAG) .

build-gate5:
	cd docker/gates/gate5_inference_preprocess && DOCKER_BUILDKIT=0 docker build -t $(REGISTRY)/cifar10-gate5:$(TAG) .

build-register:
	cd docker/gates/register_model && DOCKER_BUILDKIT=0 docker build -t $(REGISTRY)/cifar10-register:$(TAG) .

build-inference:
	cd docker/inference/preprocessor && DOCKER_BUILDKIT=0 docker build -t $(REGISTRY)/inference-preprocessor:$(TAG) .

push-all: push-train push-gates push-inference

push-train:
	docker push $(REGISTRY)/cifar10-train:$(TAG)

push-gates:
	docker push $(REGISTRY)/cifar10-gate1:$(TAG)
	docker push $(REGISTRY)/cifar10-gate3:$(TAG)
	docker push $(REGISTRY)/cifar10-gate4:$(TAG)
	docker push $(REGISTRY)/cifar10-gate5:$(TAG)
	docker push $(REGISTRY)/cifar10-register:$(TAG)

push-inference:
	docker push $(REGISTRY)/inference-preprocessor:$(TAG)

minikube-build:
	eval $$(minikube docker-env) && make all

helm-install:
	helm install mlops-platform ./helm/mlops-platform --namespace default --create-namespace --values configs/values-prod.yaml --wait

helm-upgrade:
	helm upgrade --install mlops-platform ./helm/mlops-platform --namespace default --values configs/values-prod.yaml --wait

helm-uninstall:
	helm uninstall mlops-platform --namespace default
