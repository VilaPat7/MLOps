#!/usr/bin/env python3
import argparse
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend

def verify_signature(public_key_path, signature_file, model_path, output_report):
    with open(public_key_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    with open(signature_file, 'r') as f:
        sig_data = json.load(f)
    signature = base64.b64decode(sig_data['signature'])
    with open(model_path, 'rb') as f:
        model_bytes = f.read()
    try:
        public_key.verify(
            signature,
            model_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        valid = True
    except InvalidSignature:
        valid = False
    report = {"passed": valid}
    with open(output_report, 'w') as f:
        json.dump(report, f, indent=2)
    exit(0 if valid else 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-key', required=True)
    parser.add_argument('--signature-file', required=True)
    parser.add_argument('--model-path', required=True)
    parser.add_argument('--output-report', required=True)
    args = parser.parse_args()
    verify_signature(args.public_key, args.signature_file, args.model_path, args.output_report)
