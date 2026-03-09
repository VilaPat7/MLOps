import argparse
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-key', required=True)
    parser.add_argument('--signature-file', required=True)
    parser.add_argument('--model-uri', required=True)
    parser.add_argument('--output-report', required=True)
    parser.add_argument('--output-passed', type=str, default='passed.txt')
    args = parser.parse_args()

    with open(args.public_key, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    with open(args.signature_file, 'r') as f:
        sig_data = json.load(f)
    signature = base64.b64decode(sig_data['signature'])
    message = args.model_uri.encode('utf-8')
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        passed = True
    except InvalidSignature:
        passed = False

    report = {"passed": passed}
    with open(args.output_report, 'w') as f:
        json.dump(report, f, indent=2)

    with open(args.output_passed, 'w') as f:
        f.write(str(passed))

    exit(0 if passed else 1)

if __name__ == "__main__":
    main()
