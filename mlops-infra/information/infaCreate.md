Есть 

Архитектура MLOps инфраструктуры: файлы и взаимодействия

📁 Структура проекта

text
~/mlops-infra/
├── k8s/                              # Kubernetes манифесты
│   ├── kfp/                          # Kubeflow Pipelines
│   │   ├── namespace.yaml            # Namespace для KFP
│   │   ├── kfp-full.yaml             # Полная установка KFP
│   │   └── kfp-fixed.yaml            # Исправленная версия KFP
│   ├── mlflow/                       # MLflow Tracking
│   │   ├── namespace.yaml            # Namespace для MLflow
│   │   ├── postgresql.yaml           # PostgreSQL база данных
│   │   ├── minio.yaml                # MinIO хранилище
│   │   └── mlflow-server.yaml        # MLflow Server
│   ├── istio-kserve/                 # Istio и KServe
│   │   ├── install-istio.sh          # Скрипт установки Istio
│   │   ├── kserve-setup.yaml         # Настройка KServe
│   │   └── example-inferenceservice.yaml  # Пример модели
│   └── storage/                      # Persistent Volumes
│       ├── kfp-storage.yaml          # PV для KFP
│       └── mlflow-storage.yaml       # PV для MLflow
├── scripts/                          # Скрипты управления
│   ├── deploy-kfp.sh                 # Установка KFP
│   ├── install-mlflow.sh             # Установка MLflow
│   ├── install-istio-kserve.sh       # Установка Istio+KServe
│   ├── start-all.sh                  # Запуск всей инфраструктуры
│   ├── stop-all.sh                   # Остановка всей инфраструктуры
│   ├── access-all.sh                 # Доступ к сервисам
│   ├── fix-kserve-access.sh          # Исправление доступа KServe
│   └── quick-check.sh                # Быстрая проверка
├── configs/                          # Конфигурационные файлы
├── README.md                         # Документация проекта
└── FINAL-REPORT.md                   # Финальный отчет
🔧 Файлы инфраструктуры и их назначение

1. Minikube (локальный Kubernetes)

Что: Виртуальный кластер Kubernetes на локальной машине
Файлы: Неявные (команды minikube start/stop)
Назначение: Основа для всех компонентов, оркестрация контейнеров
Взаимодействие: Предоставляет платформу для запуска всех остальных компонентов

2. Kubeflow Pipelines (KFP) - Оркестратор ML-пайплайнов

k8s/kfp/namespace.yaml

yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kubeflow-pipelines
Назначение: Изолированная среда для компонентов KFP

k8s/kfp/kfp-full.yaml

yaml
# Содержит:
- ServiceAccount (kfp-service-account)
- ClusterRoleBinding (kfp-cluster-admin) 
- Deployment: ml-pipeline-api-server
- Deployment: ml-pipeline-ui
- Service: ml-pipeline-api-server (8888)
- Service: ml-pipeline-ui (80)
Назначение: Основные компоненты KFP (API сервер + веб-интерфейс)

k8s/storage/kfp-storage.yaml

yaml
# Содержит:
- PersistentVolume: kfp-artifacts-pv
- PersistentVolumeClaim: kfp-artifacts-pvc
- ConfigMap: minio-config
- Deployment: minio
- Service: minio (9000, 9001)
Назначение: Постоянное хранилище для артефактов KFP

Взаимодействие:

text
Data Scientist → KFP UI → KFP API → Запуск пайплайна
                              ↓
                      Сохранение артефактов → MinIO (PV)
3. MLflow - Отслеживание экспериментов и моделей

k8s/mlflow/namespace.yaml

yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mlflow-system
Назначение: Изолированная среда для MLflow

k8s/mlflow/postgresql.yaml

yaml
# Содержит:
- PersistentVolume: mlflow-postgres-pv
- PersistentVolumeClaim: mlflow-postgres-pvc
- Deployment: postgresql
- Service: postgresql (5432)
Назначение: PostgreSQL база для хранения метаданных экспериментов

k8s/mlflow/minio.yaml

yaml
# Содержит:
- PersistentVolume: mlflow-minio-pv
- PersistentVolumeClaim: mlflow-minio-pvc
- Deployment: minio
- Service: minio (9000)
Назначение: S3-совместимое хранилище для артефактов моделей

k8s/mlflow/mlflow-server.yaml

yaml
# Содержит:
- Deployment: mlflow-server
- Service: mlflow-server (5000)
Назначение: MLflow Tracking Server с веб-интерфейсом

Взаимодействие:

text
ML эксперимент → Логирование в MLflow → PostgreSQL (метаданные)
                                           ↓
                                  MinIO (артефакты моделей)
4. Istio - Service Mesh для управления трафиком

k8s/istio-kserve/install-istio.sh

bash
# Устанавливает:
- Istio Control Plane
- Istio Ingress Gateway
- Enables sidecar injection
Назначение: Управление сетевым трафиком между микросервисами

Взаимодействие:

text
Внешний запрос → Istio Ingress Gateway → Маршрутизация → Сервисы
5. KServe - Serving ML-моделей

k8s/istio-kserve/kserve-setup.yaml

yaml
# Содержит:
- Namespace: kserve
- Gateway: kserve-gateway (Istio)
- VirtualService: kserve-vs
Назначение: Настройка сети для доступа к моделям

k8s/istio-kserve/example-inferenceservice.yaml

yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-iris
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: "gs://kfserving-examples/models/sklearn/1.0/model"
Назначение: Пример развернутой модели для тестирования

Взаимодействие:

text
Production запрос → Istio Gateway → KServe → InferenceService → Предсказание
6. Скрипты управления

scripts/start-all.sh

Назначение: Полный запуск всей инфраструктуры

bash
minikube start → KFP → MLflow → Istio → KServe
scripts/stop-all.sh

Назначение: Безопасная остановка инфраструктуры

bash
Остановка портов → minikube stop
scripts/access-all.sh

Назначение: Открытие доступа к UI

bash
KFP MinIO: localhost:9001
MLflow: localhost:5000
🔄 Полный цикл взаимодействия компонентов

Этап 1: Экспериментирование

text
Data Scientist → Jupyter Notebook → Логирование в MLflow
                                          ↓
                                  PostgreSQL (параметры, метрики)
                                          ↓
                                  MinIO (модели, артефакты)
Этап 2: Пайплайнизация

text
ML Engineer → KFP UI → Создание пайплайна
                         ↓
                  KFP API → Запуск задач
                         ↓
                  Сохранение результатов → KFP MinIO
                         ↓
                  Логирование метрик → MLflow
Этап 3: Деплоймент модели

text
MLflow Registry → Модель готова к деплою
                     ↓
              KServe → InferenceService
                     ↓
              Istio → Маршрутизация трафика
                     ↓
              Production → API запросы
Этап 4: Обслуживание

text
Клиент → HTTP запрос → Istio Ingress → KServe → Модель → Ответ
🔗 Связи между компонентами

Хранение данных:

text
KFP MinIO (PV) ───────┐
                       ├───> Persistent Volumes в Minikube
MLflow MinIO (PV) ────┘
                       ┌───> PostgreSQL для метаданных
MLflow PostgreSQL ────┘
Сетевое взаимодействие:

text
Внешний мир ────> Istio Ingress Gateway ────┬───> KFP UI (если работает)
                                            ├───> MLflow Server
                                            └───> KServe Inference
Логирование и трекинг:

text
KFP Пайплайн ────> Логи в MLflow ────> PostgreSQL (метаданные)
                                           ↓
                                     MinIO (артефакты)
🚀 Полный workflow MLOps

Разработка:

Эксперимент в Jupyter → Логи в MLflow
Регистрация модели в MLflow Model Registry
Создание пайплайна в KFP для автоматизации
Автоматизация:

KFP пайплайн запускается по расписанию
Обучение модели с новыми данными
Валидация и логирование в MLflow
Деплоймент:

Автоматическое создание InferenceService в KServe
Canary деплой через Istio (5% трафика на новую модель)
Мониторинг метрик качества
Обслуживание:

A/B тестирование через Istio traffic splitting
Автоматическое масштабирование через HPA
Retraining при дрифте данных
⚙️ Технические детали взаимодействия

Сеть:

bash
# 1. Внутри кластера (Service discovery)
mlflow-server.mlflow-system.svc.cluster.local:5000
minio.kubeflow-pipelines.svc.cluster.local:9000

# 2. Внешний доступ (Port-forward)
kubectl port-forward svc/mlflow-server 5000:5000 -n mlflow-system
# Теперь доступно: http://localhost:5000
Данные:

yaml
# KFP артефакты:
PersistentVolume → /data/kfp-artifacts → MinIO Pod → bucket: mlpipeline

# MLflow метаданные:
PersistentVolume → /data/mlflow-postgres → PostgreSQL → database: mlflow

# MLflow артефакты:
PersistentVolume → /data/mlflow-minio → MinIO Pod → bucket: mlflow
Безопасность:

text
Namespace изоляция:
- kubeflow-pipelines: KFP компоненты
- mlflow-system: MLflow компоненты  
- kserve: Serving моделей
- istio-system: Service mesh

Service Accounts:
- kfp-service-account: для KFP
- kserve-service-account: для KServe
📊 Мониторинг и логи

Логи компонентов:

bash
# KFP API Server
kubectl logs -n kubeflow-pipelines deployment/ml-pipeline-api-server

# MLflow Server
kubectl logs -n mlflow-system deployment/mlflow-server

# KServe Controller
kubectl logs -n kserve deployment/kserve-controller-manager
Метрики:

text
Minikube Dashboard: minikube dashboard
Kubernetes метрики: kubectl top pods
Istio метрики: доступны через Prometheus (если настроен)
🎯 Итоговая архитектура

text
                    ┌─────────────────────────────────────────────────┐
                    │               Пользователи/Клиенты              │
                    └────────────────────────┬────────────────────────┘
                                             │
                    ┌────────────────────────▼────────────────────────┐
                    │              Istio Ingress Gateway              │
                    └──────┬─────────────────┬─────────────────┬──────┘
                           │                 │                 │
        ┌─────────────────▼──┐    ┌─────────▼─────────┐    ┌──▼─────────────────┐
        │   KServe Serving   │    │    MLflow UI      │    │   KFP UI (если     │
        │   (Inference)      │    │   Experiments     │    │    работает)       │
        └─────────┬──────────┘    └─────────┬─────────┘    └──┬─────────────────┘
                  │                         │                 │
        ┌─────────▼──────────┐    ┌─────────▼─────────┐    ┌──▼─────────────────┐
        │   KServe Models    │    │  MLflow Server    │    │   KFP API Server   │
        │   (sklearn-iris)   │    │                   │    │                   │
        └────────────────────┘    └─────────┬─────────┘    └──┬─────────────────┘
                                             │                 │
        ┌────────────────────────────────────▼─────────────────▼─────────────────────┐
        │                     Kubernetes (Minikube) Cluster                          │
        ├────────────────────────────────────────────────────────────────────────────┤
        │  Persistent Storage:                                                       │
        │  - /data/kfp-artifacts    (KFP MinIO)                                      │
        │  - /data/mlflow-postgres  (MLflow PostgreSQL)                              │
        │  - /data/mlflow-minio     (MLflow MinIO)                                   │
        └────────────────────────────────────────────────────────────────────────────┘
🔧 После перезагрузки компьютера:

Быстрый старт:

bash
cd ~/mlops-infra
./scripts/start-all.sh          # Запуск всей инфраструктуры
./scripts/access-all.sh         # Открытие доступа к UI
./scripts/quick-check.sh        # Проверка состояния
Поэтапный старт:

bash
# 1. Запустить Minikube
minikube start

# 2. Запустить KFP
kubectl apply -f k8s/kfp/namespace.yaml
kubectl apply -f k8s/storage/kfp-storage.yaml
kubectl apply -f k8s/kfp/kfp-minimal.yaml

# 3. Запустить MLflow
kubectl apply -f k8s/mlflow/namespace.yaml
kubectl apply -f k8s/mlflow/

# 4. Запустить Istio и KServe
./scripts/install-istio-kserve.sh
Остановка:

bash
./scripts/stop-all.sh           # Безопасная остановка
# или
pkill -f "kubectl port-forward"
minikube stop
📈 Что получилось:

Minikube - локальный Kubernetes кластер
KFP - оркестрация ML пайплайнов (MinIO для артефактов)
MLflow - трекинг экспериментов (PostgreSQL + MinIO)
Istio - управление трафиком (Ingress Gateway)
KServe - serving моделей (InferenceService)
Все компоненты взаимодействуют через Kubernetes Service Discovery, используют Persistent Storage и управляются через единую консоль (kubectl).




Можно ли убрать kpf-fixed.yml? И то что в нем переместить в другой файл?  Или это не возможно и не нудно делать? Или это необязательно делать и можно оставить так?