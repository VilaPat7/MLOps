import argparse
import json
import mlflow
from mlflow.tracking import MlflowClient

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-uri', type=str, required=True)
    parser.add_argument('--stage', type=str, default='Staging')
    parser.add_argument('--output-report', type=str, default='register_report.json')
    args = parser.parse_args()

    client = MlflowClient()
    if args.model_uri.startswith('runs:/'):
        run_id = args.model_uri.split('/')[1]
        model_name = "cifar10-cnn-baseline"
        result = mlflow.register_model(args.model_uri, model_name)
        client.transition_model_version_stage(
            name=model_name,
            version=result.version,
            stage=args.stage
        )
        success = True
        message = f"Model registered as version {result.version} in {args.stage}"
    else:
        success = False
        message = f"Invalid model URI: {args.model_uri}"

    with open(args.output_report, 'w') as f:
        json.dump({"success": success, "message": message}, f)
    exit(0 if success else 1)

if __name__ == '__main__':
    main()
