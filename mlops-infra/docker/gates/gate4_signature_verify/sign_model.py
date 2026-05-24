import argparse
import os
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import mlflow
import tempfile

def compute_model_hash(model_path: str) -> bytes:
    hasher = hashlib.sha256()
    for root, _, files in os.walk(model_path):
        for file in sorted(files):
            if file == "signature.sig":
                continue
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                hasher.update(f.read())
    hash_bytes = hasher.digest()
    print(f"[DEBUG] Model hash (hex): {hash_bytes.hex()}")
    return hash_bytes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--private-key', required=True, help='Path to private key PEM file')
    parser.add_argument('--model-uri', required=True, help='MLflow model URI (e.g., runs:/<run_id>/model)')
    parser.add_argument('--output-signature', required=True, help='Output file for signature (binary)')
    args = parser.parse_args()

    with open(args.private_key, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Downloading model from {args.model_uri} ...")
        local_path = mlflow.artifacts.download_artifacts(artifact_uri=args.model_uri, dst_path=tmpdir)
        model_path = local_path

        model_hash = compute_model_hash(model_path)

        signature = private_key.sign(
            model_hash,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        with open(args.output_signature, "wb") as f:
            f.write(signature)

        print(f"Signature saved to {args.output_signature}")

if __name__ == "__main__":
    main()
