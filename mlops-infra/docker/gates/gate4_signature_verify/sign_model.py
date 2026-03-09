import argparse
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--private-key', required=True)
    parser.add_argument('--model-uri', required=True)
    parser.add_argument('--output-signature', required=True)
    args = parser.parse_args()

    with open(args.private_key, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    message = args.model_uri.encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    with open(args.output_signature, 'w') as f:
        json.dump({"signature": signature_b64, "model_uri": args.model_uri}, f, indent=2)

if __name__ == "__main__":
    main()
