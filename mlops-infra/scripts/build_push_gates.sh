#!/bin/bash
set -e

# Переходим в корень проекта
cd "$(dirname "$0")/.."

echo "Building images from $(pwd)"

docker build -t cifar10-train:latest docker/train
docker build -t cifar10-gate1:latest docker/gates/gate1_data_validation
docker build -t cifar10-gate3:latest docker/gates/gate3_model_validation
docker build -t cifar10-gate4:latest docker/gates/gate4_signature_verify
docker build -t cifar10-gate5:latest docker/gates/gate5_inference_preprocess
docker build -t cifar10-register-model:latest docker/gates/register_model

echo "All images built successfully."
