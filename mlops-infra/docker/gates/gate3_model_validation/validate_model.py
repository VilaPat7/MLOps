import argparse
import tensorflow as tf
import json
import mlflow
import numpy as np

def load_model(model_uri):
    local_path = mlflow.artifacts.download_artifacts(artifact_uri=model_uri)
    return tf.keras.models.load_model(local_path)

def evaluate_model(model, test_data_path):
    data = np.load(test_data_path)
    x_test = data['x_test']
    y_test = data['y_test']
    loss, acc = model.evaluate(x_test, y_test, verbose=0)
    return acc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-uri', type=str, required=True)
    parser.add_argument('--test-data', type=str, required=True)
    parser.add_argument('--accuracy-threshold', type=float, default=0.7)
    parser.add_argument('--output-report', type=str, default='model_validation.json')
    parser.add_argument('--output-passed', type=str, default='passed.txt')
    args = parser.parse_args()

    model = load_model(args.model_uri)
    accuracy = evaluate_model(model, args.test_data)

    passed = accuracy >= args.accuracy_threshold
    report = {
        "passed": passed,
        "accuracy": float(accuracy),
        "threshold": args.accuracy_threshold,
        "model_uri": args.model_uri
    }
    with open(args.output_report, 'w') as f:
        json.dump(report, f, indent=2)

    with open(args.output_passed, 'w') as f:
        f.write(str(passed))

    exit(0 if passed else 1)

if __name__ == "__main__":
    main()
