#!/bin/bash
set -e
echo "=== Destroying MLOps Platform ==="
make helm-uninstall
minikube stop
echo "Destroy completed."
