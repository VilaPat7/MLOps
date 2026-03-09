~/mlops-infra/
├── docker/
│   ├── train/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── train.py
│   └── gates/
│       ├── gate1_data_validation/
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── validate_data.py
│       ├── gate3_model_validation/
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── validate_model.py
│       ├── gate4_signature_verify/
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   ├── sign_model.py
│       │   └── verify_signature.py
│       ├── gate5_inference_preprocess/
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   ├── preprocess.py
│       │   └── anomaly_detector.pkl
│       └── register_model/
│           ├── Dockerfile
│           ├── requirements.txt
│           └── register.py
├── k8s/
│   ├── kfp/
│   │   └── components/
│   │       ├── gate1_data_validation.yaml
│   │       ├── gate3_model_validation.yaml
│   │       ├── gate4_sign_model.yaml
│   │       ├── gate4_verify_signature.yaml
│   │       ├── train.yaml
│   │       ├── train_dp.yaml
│   │       └── register_model.yaml
│   └── secrets/
│       └── signing-keys.yaml
├── scripts/
│   ├── generate_keys.sh
│   ├── build_push_gates.sh
│   └── run-baseline.sh
├── baseline/
│   └── train-job.yaml
└── pipelines/
    └── secure_training_pipeline.py