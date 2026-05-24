import os
from mlflow import MlflowClient

run_id = "0544b6cf676b466eb4e12bff72ed22a6"

local_path = os.path.expanduser("~/mlops-infra/docker/gates/gate4_signature_verify/signature.sig")

artifact_path = "model"

client = MlflowClient()

client.log_artifact(run_id, local_path, artifact_path)
print(f"The {local_path} file has been successfully uploaded to run {run_id}, path:{artifact_path}")
