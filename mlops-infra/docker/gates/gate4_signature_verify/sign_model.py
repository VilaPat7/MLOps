#!/usr/bin/env python3
import argparse
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

def sign_model(private_key_path, model_path, output_signature):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    with open(model_path, "rb") as f:
        model_bytes = f.read()
    signature = private_key.sign(
        model_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    with open(output_signature, 'w') as f:
        json.dump({"signature": signature_b64}, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--private-key', required=True)
    parser.add_argument('--model-path', required=True)
    parser.add_argument('--output-signature', required=True)
    args = parser.parse_args()
    sign_model(args.private_key, args.model_path, args.output_signature)
