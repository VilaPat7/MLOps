#!/bin/bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
echo "Keys generated in ./keys/"
kubectl create secret generic model-signing-keys --from-file=private.pem=keys/private.pem --from-file=public.pem=keys/public.pem -n default
