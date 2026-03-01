#!/bin/bash
set -e

# Образ обучения (пересборка с новыми зависимостями)
docker build -t cifar10-train:latest docker/train

# Гейты
docker build -t cifar10-gate1:latest docker/gates/gate1_data_validation
docker build -t cifar10-gate3:latest docker/gates/gate3_model_validation
docker build -t cifar10-gate4:latest docker/gates/gate4_signature_verify
docker build -t cifar10-gate5:latest docker/gates/gate5_inference_preprocess

echo "All images built successfully."
# Если есть registry, можно выполнить push:
# docker tag cifar10-train:latest your-registry/cifar10-train:latest && docker push ...
