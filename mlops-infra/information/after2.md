~/mlops-infra/
├── docker/
│   ├── train/                                 # Образ для обучения (модифицирован)
│   │   ├── Dockerfile                          # Базовый образ tensorflow/tensorflow:2.13.0-gpu + зависимости (включая opacus)
│   │   └── train.py                             # Скрипт обучения с поддержкой DP и чтением параметров из env/аргументов
│   └── gates/                                   # Новые компоненты безопасности
│       ├── gate1_data_validation/                # Gate 1: проверка целостности данных (data poisoning)
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── validate_data.py
│       ├── gate3_model_validation/                # Gate 3: проверка качества модели (accuracy > порог)
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── validate_model.py
│       ├── gate4_signature_verify/                # Gate 4: цифровая подпись модели
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   ├── sign_model.py
│       │   └── verify_signature.py
│       └── gate5_inference_preprocess/            # Gate 5: защита инференса (валидация + детекция аномалий)
│           ├── Dockerfile
│           ├── requirements.txt
│           ├── preprocess.py
│           └── anomaly_detector.pkl                # Предобученная модель детектора (нужно создать отдельно)
├── k8s/
│   ├── kfp/
│   │   └── components/                           # YAML-описания компонентов для Kubeflow Pipelines
│   │       ├── gate1_data_validation.yaml
│   │       ├── gate3_model_validation.yaml
│   │       ├── gate4_sign_model.yaml
│   │       ├── gate4_verify_signature.yaml
│   │       ├── train.yaml                          # Компонент обучения без DP
│   │       └── train_dp.yaml                        # Компонент обучения с DP
│   └── secrets/                                    # Секреты Kubernetes
│       └── signing-keys.yaml                         # Манифест секрета с ключами подписи (создаётся скриптом)
├── scripts/
│   ├── generate_keys.sh                            # Генерация пары RSA-ключей и создание секрета
│   ├── build_push_gates.sh                         # Сборка всех Docker-образов локально
│   └── run-baseline.sh                              # Существующий скрипт запуска базового пайплайна (без изменений)
└── baseline/
    └── train-job.yaml                               # Существующий job для обучения (без изменений)