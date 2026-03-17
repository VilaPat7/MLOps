import argparse
import os
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

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
    parser.add_argument('--private-key', required=True)
    parser.add_argument('--model-path', required=True)
    parser.add_argument('--output-signature', required=True)
    args = parser.parse_args()

    with open(args.private_key, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    model_hash = compute_model_hash(args.model_path)

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
