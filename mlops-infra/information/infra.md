I. БАЗОВАЯ ИНФРАСТРУКТУРА
1. Minikube (локальный Kubernetes кластер)

text
Назначение: Основа для всех компонентов
Версия: latest
Ресурсы: 8GB RAM, 4 CPU, 50GB диска
Аддоны: metrics-server, dashboard, ingress
Состояние: Running (проверить: minikube status)
Доступ: kubectl, minikube dashboard
2. Kubernetes Namespaces (изоляция компонентов)

text
- kubeflow-pipelines    - KFP компоненты
- mlflow-system         - MLflow + PostgreSQL + MinIO
- istio-system          - Istio service mesh  
- kserve                - KServe модели
- kserve-system         - KServe контроллер
- monitoring            - Prometheus + Grafana
II. MLOps КОМПОНЕНТЫ
3. Kubeflow Pipelines (KFP) - Оркестратор

text
Компоненты:
  - ml-pipeline-api-server (API сервер KFP)
  - ml-pipeline-ui (Веб-интерфейс KFP)
  - minio-kfp (S3-хранилище для артефактов KFP)

Порты:
  - KFP API: 8888 (внутренний)
  - KFP UI: 80 (внутренний)
  - MinIO Console: 9001

Хранение:
  - PVC: kfp-artifacts-pvc
  - PV: kfp-artifacts-pv
  - Путь: /data/kfp-artifacts

Данные: Артефакты пайплайнов, метаданные
4. MLflow - Трекинг экспериментов

text
Компоненты:
  - mlflow-server (Tracking Server)
  - postgresql (БД для метаданных)
  - minio-mlflow (S3 для артефактов моделей)

Порты:
  - MLflow UI: 5000
  - PostgreSQL: 5432 (внутренний)
  - MinIO: 9000, 9001 (внутренний)

Хранение:
  - PVC: mlflow-postgres-pvc, mlflow-minio-pvc
  - Данные: 
    * PostgreSQL: метаданные экспериментов
    * MinIO: модели, артефакты, метрики

Конфигурация:
  - БД: postgresql://mlflow:mlflow@postgresql:5432/mlflow
  - Артефакты: s3://mlflow/
  - Endpoint: http://minio:9000
5. PostgreSQL - База данных MLflow

text
Версия: 13
Конфигурация:
  - Database: mlflow
  - User: mlflow
  - Password: mlflow
Объем: 5GB
Назначение: Хранение метаданных экспериментов
6. MinIO (два экземпляра)

text
а) Для MLflow:
   - Bucket: mlflow
   - Доступ: http://minio.mlflow-system:9000
   - Console: http://localhost:9001
   - Credentials: minioadmin/minioadmin

б) Для KFP:
   - Bucket: mlpipeline  
   - Доступ: http://minio.kubeflow-pipelines:9000
   - Console: http://localhost:9002
   - Credentials: minioadmin/minioadmin
III. SERVING И СЕТЬ
7. Istio - Service Mesh

text
Компоненты:
  - istiod (Control Plane)
  - istio-ingressgateway (Ingress Gateway)
  - istio-egressgateway (Egress Gateway)

Назначение:
  - Управление трафиком
  - Load balancing
  - Service discovery
  - Security (mTLS)

Порты:
  - Ingress Gateway: 80, 443
  - Проброс: localhost:8080 → istio-ingressgateway:80
8. KServe - Model Serving

text
Компоненты:
  - kserve-controller-manager (управление)
  - InferenceService (ресурсы моделей)

Пример модели:
  - Имя: sklearn-iris
  - Тип: sklearn
  - Source: gs://kfserving-examples/models/sklearn/1.0/model
  - Namespace: kserve

API Endpoint:
  - /v1/models/<model-name>:predict
  - Host header: sklearn-iris.kserve.example.com
IV. МОНИТОРИНГ
9. Prometheus - Сбор метрик

text
Назначение: Сбор и хранение метрик
Версия: latest
Порты: 9090
Хранение: 10GB
Конфигурация: 
  - scrape_interval: 15s
  - Target: Kubernetes pods, services
Доступ: http://localhost:9090
10. Grafana - Визуализация

text
Назначение: Дашборды мониторинга
Версия: latest
Порты: 3000
Конфигурация:
  - Источник данных: Prometheus
  - Логин: admin/admin
  - Дашборды: Kubernetes, MLflow, MinIO
Доступ: http://localhost:3000
V. СКРИПТЫ УПРАВЛЕНИЯ
11. Основные скрипты:

text
check-and-start.sh     - Проверка и запуск всей инфраструктуры
access-all.sh          - Открытие доступа ко всем UI (порт-форвардинг)
stop-all.sh            - Безопасная остановка
quick-status.sh        - Быстрая проверка статуса
install-istio-kserve.sh - Установка Istio + KServe
12. Baseline пайплайн:

text
run-baseline.sh        - Запуск обучения CIFAR-10 модели
test-model.sh          - Тестирование развернутой модели
VI. ФАЙЛОВАЯ СТРУКТУРА
text
~/mlops-infra/
├── k8s/                           # Kubernetes манифесты
│   ├── kfp/                       # Kubeflow Pipelines
│   │   ├── namespace.yaml
│   │   ├── kfp-minimal.yaml
│   │   └── kfp-full.yaml
│   ├── storage/                   # Persistent Volumes
│   │   ├── kfp-storage.yaml
│   │   └── mlflow-storage.yaml
│   ├── mlflow/                    # MLflow инфраструктура
│   │   ├── namespace.yaml
│   │   ├── postgresql.yaml
│   │   ├── minio.yaml
│   │   └── mlflow-server.yaml
│   ├── istio-kserve/              # Istio + KServe
│   │   ├── kserve-setup.yaml
│   │   └── example-inferenceservice.yaml
│   └── monitoring/                # Мониторинг
│       ├── prometheus.yaml
│       └── grafana.yaml
├── scripts/                       # Скрипты управления
│   ├── check-and-start.sh
│   ├── access-all.sh
│   ├── stop-all.sh
│   ├── quick-status.sh
│   ├── install-istio-kserve.sh
│   ├── run-baseline.sh
│   └── test-model.sh
├── docker/                        # Docker образы
│   ├── train/
│   │   ├── Dockerfile
│   │   └── train.py
│   └── deploy/
│       ├── Dockerfile
│       └── deploy.sh
├── pipelines/                     # KFP пайплайны
│   ├── cifar10_baseline.py
│   ├── cifar10_baseline_pipeline.yaml
│   └── components/
├── istio-1.19.0/                  # Istio CLI и файлы
├── README.md                      # Основная документация
└── BASELINE-README.md            # Baseline конфигурация
VII. СЕТЕВАЯ АРХИТЕКТУРА
Service Discovery (внутри кластера):

text
mlflow-server.mlflow-system.svc.cluster.local:5000
postgresql.mlflow-system.svc.cluster.local:5432
minio.mlflow-system.svc.cluster.local:9000
minio.kubeflow-pipelines.svc.cluster.local:9000
istio-ingressgateway.istio-system.svc.cluster.local:80
External Access (порт-форвардинг):

text
localhost:5000    → MLflow UI
localhost:9001    → MinIO Console (MLflow)
localhost:9002    → MinIO Console (KFP)
localhost:8080    → Istio Ingress (KServe)
localhost:3000    → Grafana
localhost:9090    → Prometheus
localhost:8081    → KFP UI (если установлен)
VIII. ДАННЫЕ И ХРАНЕНИЕ
Persistent Volumes:

text
1. KFP артефакты:
   - PV: kfp-artifacts-pv (20GB)
   - PVC: kfp-artifacts-pvc
   - Путь в Minikube: /data/kfp-artifacts

2. MLflow PostgreSQL:
   - PVC: mlflow-postgres-pvc (5GB)
   - Данные: метаданные экспериментов

3. MLflow MinIO:
   - PVC: mlflow-minio-pvc (10GB)
   - Данные: модели, артефакты
Конфигурация MinIO:

text
- Регион: us-east-1
- Access Key: minioadmin
- Secret Key: minioadmin
- Бакеты: mlflow, mlpipeline
- Политика: public для чтения
IX. БЕЗОПАСНОСТЬ
Service Accounts:

text
- default (в каждом namespace)
- kfp-service-account (для KFP)
- kserve-service-account (для KServe)
Network Policies:

text
- Изоляция по namespace
- Ingress через Istio Gateway
- Egress разрешен для всех
X. МОНИТОРИНГ И ЛОГИ
Логи компонентов:

text
MLflow:        kubectl logs -n mlflow-system deployment/mlflow-server
PostgreSQL:    kubectl logs -n mlflow-system deployment/postgresql
KFP API:       kubectl logs -n kubeflow-pipelines deployment/ml-pipeline-api-server
KServe:        kubectl logs -n kserve-system deployment/kserve-controller-manager
Метрики:

text
Minikube Dashboard: minikube dashboard
Kubernetes: kubectl top pods
Prometheus: localhost:9090
Grafana: localhost:3000