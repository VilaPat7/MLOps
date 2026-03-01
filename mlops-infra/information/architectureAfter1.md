📁 Текущая архитектура проекта (кратко)
Общая схема
Minikube – локальный кластер Kubernetes.

Kubeflow Pipelines (KFP) – оркестрация пайплайнов обучения (опционально).

MLflow Tracking – логирование экспериментов, хранение моделей.

PostgreSQL – метаданные.

MinIO – S3-совместимое хранилище артефактов (модели, данные).

TensorFlow Serving – развёртывание модели (вместо KServe).

PVC model-pvc – постоянный том для хранения модели.

Job model-loader – копирует модель из MinIO в PVC.

Istio – остался для других сервисов (не влияет на serving).

Prometheus/Grafana – мониторинг (опционально).

Структура папок и ключевые файлы
text
~/mlops-infra/
├── README.md                          # Общая документация
├── BASELINE-README.md                  # Документация по CIFAR-10 baseline
├── istio-1.19.0/                       # Установочные файлы Istio (не используется активно)
├── k8s/                                 # Манифесты Kubernetes
│   ├── kfp/                             # Kubeflow Pipelines
│   │   ├── namespace.yaml
│   │   └── kfp-minimal.yaml
│   ├── mlflow/                           # MLflow
│   │   ├── namespace.yaml
│   │   ├── postgresql.yaml
│   │   ├── minio.yaml
│   │   └── mlflow-server.yaml
│   ├── tf-serving/                        # TensorFlow Serving (новое)
│   │   ├── model-pvc.yaml                  # PVC для модели
│   │   ├── model-loader-job.yaml            # Job копирования модели из MinIO
│   │   ├── tf-serving-deployment.yaml       # Deployment TensorFlow Serving
│   │   └── tf-serving-service.yaml          # Service для доступа к модели
│   ├── monitoring/                          # Prometheus + Grafana
│   │   ├── prometheus.yaml
│   │   └── grafana.yaml
│   └── storage/                             # (опционально, не используется)
├── scripts/                             # Bash-скрипты
│   ├── check-and-start.sh                 # Проверка и запуск инфраструктуры
│   ├── access-all.sh                       # Port-forward ко всем UI
│   ├── stop-all.sh                          # Остановка port-forward и Minikube
│   ├── quick-status.sh                      # Краткий статус кластера
│   ├── install-istio-kserve.sh              # Установка Istio (KServe убран)
│   ├── run-baseline.sh                       # Полный пайплайн (обучение → деплой)
│   └── test-model.sh                          # Тестирование модели
├── docker/                               # Docker-образы
│   └── train/                               # Образ для обучения
│       ├── Dockerfile
│       └── train.py                           # Скрипт обучения CIFAR-10 с MLflow
└── baseline/                              # Файлы baseline
    └── train-job.yaml                        # Kubernetes Job для обучения
