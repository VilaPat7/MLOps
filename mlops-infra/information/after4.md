Подробное описание этапов 1–4 и итоговая архитектура
Этап 1: Подготовка инфраструктуры и базового решения
Minikube запущен с параметрами: --cpus=6 --memory=12288 --addons=ingress --cni=bridge.

Установлены базовые компоненты:

MLflow (namespace mlflow-system):

PostgreSQL (база данных)

MinIO (S3-хранилище артефактов)

MLflow Tracking Server (порт 5000)

TensorFlow Serving (namespace default):

Deployment cifar10-tf-serving для базового инференса

PVC для модели, Job для загрузки модели из MinIO

Istio (установлен, sidecar injection включён в namespace default)

Prometheus + Grafana (namespace monitoring) – установлены, но не активно используются.

Создан базовый пайплайн обучения (run-baseline.sh), который обучает модель CIFAR-10 и сохраняет в MinIO, логирует в MLflow.

Этап 2: Разработка компонентов Security Gates
Созданы Docker-образы для гейтов в docker/gates/:

Gate 1 (gate1_data_validation): проверка целостности данных (data poisoning).

Gate 2 интегрирован в train.py как опция --enable-dp (дифференциальная приватность через Opacus).

Gate 3 (gate3_model_validation): проверка качества модели на тестовых данных.

Gate 4 (gate4_signature_verify): подпись и верификация модели (RSA-ключи). Скрипты sign_model.py и verify_signature.py.

Gate 5 (gate5_inference_preprocess): препроцессинг запросов и детекция аномалий (Pydantic + модель-заглушка anomaly_detector.pkl).

register_model: регистрация модели в MLflow Model Registry.

Сгенерированы ключи (generate_keys.sh): private_key.pem, public_key.pem.

Этап 3: Построение тренировочного пайплайна
Написан скрипт secure_training_pipeline.py на KFP SDK, определяющий граф:

Gate 1 (Data Validation) → Training (с/без DP) → Gate 3 (Model Validation) → Signing → Gate 4 (Verification) → Registration.

Пайплайн скомпилирован в secure_pipeline.tar.gz. Из-за проблем с Kubeflow (неработающий UI) он не запускался, но все артефакты созданы.

Этап 4: Создание защищённого сервиса инференса
Разработан Docker-образ inference-preprocessor в docker/inference/preprocessor/:

model_loader.py: загружает модель из MLflow Model Registry (стадия Production), проверяет подпись (Gate 4), сохраняет в /shared/models/1.

prepost_processor.py: Pydantic-валидация, детекция аномалий (Gate 5) с использованием anomaly_detector.pkl (заглушка на DummyClassifier).

main.py: FastAPI-сервер с эндпоинтом /v1/models/cifar10:predict, который принимает запрос, вызывает gRPC к TensorFlow Serving и возвращает ответ.

Написаны манифесты Kubernetes в k8s/inference/:

secret-mlflow.yaml: секрет с публичным ключом (public_key.pem) и данными MinIO.

deployment.yaml: под с двумя контейнерами (preprocessor и tf-serving), общая папка emptyDir, ресурсы requests (после оптимизации 100m/256Mi), пробы готовности.

service.yaml: ClusterIP для доступа к preprocessor (порт 80).

hpa.yaml: горизонтальное автоскейлинг (целевая загрузка CPU 70%).

Настроены политики Istio (Gate 6) в istio/:

request-auth.yaml: проверка JWT-токенов (issuer testing@secure.istio.io, jwksUri из репозитория Istio).

auth-policy.yaml: разрешён доступ только с валидным JWT.

В ходе выполнения решены проблемы:

Нехватка ресурсов – очистка кластера от мусорных подов (Kubeflow, старые версии).

Пустой файл anomaly_detector.pkl – заменён на корректный pickle с DummyClassifier.

Ошибка Invalid Host header при доступе к MLflow – отключён Istio sidecar в namespace mlflow-system.

Итог: поды инференса запускаются, проходят проверки (Gate 4,5), эндпоинт доступен и защищён JWT.

Итоговая структура проекта с комментариями
text
~/mlops-infra/
├── README.md
├── BASELINE-README.md
├── istio-1.19.0/                               # Дистрибутив Istio (установочные файлы)
├── k8s/                                         # Манифесты Kubernetes
│   ├── kfp/                                     # Kubeflow Pipelines (не используется, но сохранено)
│   ├── mlflow/                                   # MLflow
│   │   ├── namespace.yaml                        # Создаёт namespace mlflow-system
│   │   ├── postgresql.yaml                       # PostgreSQL StatefulSet
│   │   ├── minio.yaml                             # MinIO Deployment
│   │   └── mlflow-server.yaml                     # MLflow Tracking Server Deployment
│   ├── tf-serving/                                # Базовый инференс
│   │   ├── model-pvc.yaml                          # PVC для модели
│   │   ├── model-loader-job.yaml                    # Job для копирования модели из MinIO
│   │   ├── tf-serving-deployment.yaml                 # Deployment TensorFlow Serving
│   │   └── tf-serving-service.yaml                    # Service для базового инференса
│   ├── monitoring/                                # Prometheus + Grafana (установлены, не используются)
│   └── inference/                                 # Защищённый инференс (Этап 4)
│       ├── secret-mlflow.yaml                      # Секрет с ключом и данными MinIO
│       ├── deployment.yaml                          # Deployment с preprocessor и tf-serving
│       ├── service.yaml                             # Service для доступа
│       └── hpa.yaml                                 # HorizontalPodAutoscaler
├── scripts/                                      # Вспомогательные скрипты
│   ├── check-and-start.sh                          # Проверка и запуск инфраструктуры
│   ├── access-all.sh                                # Port-forward ко всем UI
│   ├── stop-all.sh                                  # Остановка port-forward и Minikube
│   ├── quick-status.sh                              # Краткий статус
│   ├── install-istio-kserve.sh                      # Установка Istio/KServe
│   ├── run-baseline.sh                               # Запуск базового пайплайна
│   ├── test-model.sh                                 # Тестирование базового инференса
│   ├── generate_keys.sh                              # Генерация ключей RSA
│   └── build_push_gates.sh                           # Сборка образов гейтов
├── docker/                                       # Docker-образы
│   ├── train/                                      # Обучение модели
│   ├── gates/                                       # Гейты 1,3,4,5, register
│   └── inference/                                   # Защищённый инференс
│       └── preprocessor/
│           ├── Dockerfile
│           ├── requirements.txt
│           ├── main.py
│           ├── model_loader.py
│           ├── prepost_processor.py
│           └── anomaly_detector.pkl
├── baseline/                                      # Базовый пайплайн (train-job.yaml)
├── pipelines/                                      # Пайплайны Kubeflow
│   ├── secure_training_pipeline.py
│   └── secure_pipeline.tar.gz
└── istio/                                          # Политики безопасности Istio
    ├── request-auth.yaml
    └── auth-policy.yaml
Взаимодействие компонентов после Этапа 4
Обучение (базовое или пайплайн) → модель сохраняется в MinIO, логируется в MLflow Tracking. При использовании пайплайна создаётся подпись.

Модель переводится в статус Production в MLflow Model Registry (вручную).

Защищённый инференс:

При старте preprocessor загружает модель из MLflow (через MinIO), проверяет подпись (Gate 4) и сохраняет в общую папку.

TensorFlow Serving читает модель из той же папки.

Входящие HTTP-запросы:

Istio sidecar проверяет JWT (Gate 6) – без токена возвращает 403.

Preprocessor валидирует JSON, прогоняет через детектор аномалий (Gate 5) и отправляет gRPC в TF Serving.

Результат возвращается клиенту.

Базовый инференс (отдельный TF Serving) доступен для сравнения.

















2. Подробное описание этапов 1–4 и итоговая архитектура
Этап 1: Подготовка инфраструктуры и базового решения
Цель: Развернуть базовую MLOps-инфраструктуру в Minikube и создать простой пайплайн обучения без защиты.

Что сделано:

Запущен Minikube с параметрами: --cpus=6 --memory=12288 --addons=ingress --cni=bridge.

Установлены ключевые компоненты:

MLflow (namespace mlflow-system):

PostgreSQL – база данных для метаданных экспериментов.

MinIO – S3-совместимое хранилище для артефактов моделей.

MLflow Tracking Server – сервер для логирования параметров, метрик и моделей.

TensorFlow Serving (namespace default):

Отдельный Deployment cifar10-tf-serving для базового инференса.

PVC для хранения модели, Job model-loader для копирования модели из MinIO.

Istio – установлен для будущей безопасности (пока не активен).

Prometheus + Grafana – для мониторинга (установлены, но не использовались).

Создан скрипт run-baseline.sh, который запускает обучение модели CIFAR-10 через Kubernetes Job (train-job.yaml), сохраняет модель в MinIO и логирует в MLflow.

Этап 2: Разработка компонентов Security Gates
Цель: Создать контейнеризованные компоненты (гейты) для проверок безопасности.

Что сделано:

Созданы Docker-образы в docker/gates/:

Gate 1 (gate1_data_validation): проверка целостности данных (data poisoning) – анализ распределения меток.

Gate 2 – интегрирован в обучение как опция --enable-dp (дифференциальная приватность через Opacus).

Gate 3 (gate3_model_validation): проверка качества модели (accuracy на тестовых данных).

Gate 4 (gate4_signature_verify):

sign_model.py – подписывание модели с помощью RSA-ключа.

verify_signature.py – проверка подписи.

Gate 5 (gate5_inference_preprocess):

Pydantic-валидация входящих запросов.

Детекция аномалий через модель-заглушку anomaly_detector.pkl.

register_model – регистрация модели в MLflow Model Registry со стадией Staging.

Сгенерированы ключи (generate_keys.sh): private_key.pem (приватный) и public_key.pem (публичный).

Этап 3: Построение тренировочного пайплайна
Цель: Оркестровать выполнение гейтов в едином пайплайне обучения.

Что сделано:

Написан скрипт secure_training_pipeline.py с использованием KFP SDK, который определяет граф:

Data Validation (Gate 1) → Training (с/без DP) → Model Validation (Gate 3) → Signing → Verification (Gate 4) → Registration.

Реализована условная логика остановки пайплайна при неудаче любого гейта.

Пайплайн скомпилирован в secure_pipeline.tar.gz. Из-за проблем с Kubeflow (неработающий UI) он не был запущен, но все артефакты созданы.

Этап 4: Создание защищённого сервиса инференса (текущий)
Цель: Развернуть масштабируемый и безопасный эндпоинт для предсказаний, интегрировав Gates 4, 5 и 6.

Что сделано:

Разработан Docker-образ inference-preprocessor в docker/inference/preprocessor/:

model_loader.py:

При старте загружает модель из MLflow Model Registry (стадия Production).

Проверяет цифровую подпись (Gate 4) с помощью публичного ключа.

Сохраняет модель в общую папку /shared/models/1.

prepost_processor.py:

Pydantic-модель для валидации входящих JSON (Gate 5).

Детектор аномалий на основе DummyClassifier (заглушка).

Функции пред- и постобработки (нормализация, softmax).

main.py: FastAPI-сервер с эндпоинтом /v1/models/cifar10:predict. Обрабатывает запрос: валидация, детекция, gRPC-вызов к TF Serving, постобработка.

Написаны Kubernetes-манифесты в k8s/inference/:

secret-mlflow.yaml – содержит публичный ключ (public_key.pem) и учётные данные MinIO.

deployment.yaml – под с двумя контейнерами:

preprocessor (кастомный образ)

tf-serving (стандартный tensorflow/serving)

Общая папка emptyDir для модели.

Ресурсы requests (после оптимизации: 100m CPU, 256Mi memory).

Readiness и liveness пробы.

service.yaml – ClusterIP для доступа к preprocessor (порт 80 → 8080).

hpa.yaml – горизонтальное автоскейлинг по CPU (целевая загрузка 70%).

Настроены политики Istio (Gate 6) в istio/:

request-auth.yaml – проверка JWT-токенов на всех входящих запросах к сервису cifar10-inference.

auth-policy.yaml – разрешён доступ только запросам с валидным JWT (любой principal).

В ходе выполнения решены проблемы:

Нехватка ресурсов – очистка кластера от мусорных подов (Kubeflow, старые версии).

Ошибка EOFError с детектором – замена на корректный pickle с DummyClassifier.

Ошибка Invalid Host header при доступе к MLflow – отключение Istio sidecar в namespace mlflow-system.

После исправления всех ошибок поды должны запускаться и успешно обслуживать запросы.

Итоговая структура проекта с комментариями
text
~/mlops-infra/
├── README.md                                  # Основная документация
├── BASELINE-README.md                          # Документация по базовому решению
├── istio-1.19.0/                               # Дистрибутив Istio (установочные файлы)
│
├── k8s/                                         # Все манифесты Kubernetes
│   ├── kfp/                                     # Kubeflow Pipelines (не используется, но сохранено)
│   ├── mlflow/                                   # MLflow
│   │   ├── namespace.yaml                        # Создаёт namespace mlflow-system
│   │   ├── postgresql.yaml                        # PostgreSQL StatefulSet
│   │   ├── minio.yaml                             # MinIO Deployment
│   │   └── mlflow-server.yaml                      # MLflow Tracking Server Deployment
│   ├── tf-serving/                                # Базовый инференс
│   │   ├── model-pvc.yaml                          # PVC для модели
│   │   ├── model-loader-job.yaml                    # Job для копирования модели из MinIO
│   │   ├── tf-serving-deployment.yaml                 # Deployment TensorFlow Serving
│   │   └── tf-serving-service.yaml                    # Service для базового инференса
│   ├── monitoring/                                # Prometheus + Grafana (установлены, не используются)
│   └── inference/                                 # Защищённый инференс (Этап 4)
│       ├── secret-mlflow.yaml                      # Секрет с публичным ключом и данными MinIO
│       ├── deployment.yaml                          # Deployment с preprocessor и tf-serving
│       ├── service.yaml                             # Service для доступа
│       └── hpa.yaml                                 # HorizontalPodAutoscaler
│
├── scripts/                                      # Вспомогательные bash-скрипты
│   ├── check-and-start.sh                          # Проверка и запуск инфраструктуры
│   ├── access-all.sh                                # Port-forward ко всем UI
│   ├── stop-all.sh                                  # Остановка port-forward и Minikube
│   ├── quick-status.sh                              # Краткий статус компонентов
│   ├── install-istio-kserve.sh                      # Установка Istio/KServe (не используется)
│   ├── run-baseline.sh                               # Запуск базового пайплайна обучения
│   ├── test-model.sh                                 # Тестирование базового инференса
│   ├── generate_keys.sh                              # Генерация ключей RSA
│   └── build_push_gates.sh                           # Сборка образов гейтов
│
├── docker/                                       # Docker-образы
│   ├── train/                                      # Обучение модели
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── train.py
│   ├── gates/                                       # Гейты 1,3,4,5, register
│   │   ├── gate1_data_validation/
│   │   ├── gate3_model_validation/
│   │   ├── gate4_signature_verify/
│   │   ├── gate5_inference_preprocess/
│   │   └── register_model/
│   └── inference/                                   # Защищённый инференс
│       └── preprocessor/
│           ├── Dockerfile
│           ├── requirements.txt
│           ├── main.py
│           ├── model_loader.py
│           ├── prepost_processor.py
│           └── anomaly_detector.pkl
│
├── baseline/                                      # Базовый пайплайн обучения
│   └── train-job.yaml                               # Kubernetes Job для обучения
│
├── pipelines/                                      # Скрипты пайплайнов Kubeflow
│   ├── secure_training_pipeline.py                   # Определение пайплайна с гейтами
│   └── secure_pipeline.tar.gz                        # Скомпилированный пайплайн
│
└── istio/                                          # Политики безопасности Istio
    ├── request-auth.yaml                             # RequestAuthentication (JWT)
    └── auth-policy.yaml                              # AuthorizationPolicy (доступ только с JWT)
Взаимодействие компонентов после Этапа 4
Обучение (базовое или через пайплайн) → модель сохраняется в MinIO, логируется в MLflow Tracking. При использовании пайплайна создаётся подпись signature.sig.

Модель вручную (или через пайплайн) переводится в статус Production в MLflow Model Registry.

Защищённый инференс:

При старте preprocessor:

Загружает модель из MLflow (через MinIO) по S3.

Проверяет подпись (Gate 4) с помощью публичного ключа из секрета.

Сохраняет модель в общую папку /shared/models/1.

tf-serving автоматически загружает модель из /models/1 (так как папка смонтирована).

Входящий HTTP-запрос:

Проходит через Istio sidecar, который проверяет JWT-токен (Gate 6). Без токена – 403.

Если токен валиден, запрос попадает в preprocessor.

preprocessor валидирует JSON (Pydantic) и прогоняет через детектор аномалий (Gate 5). При аномалии – 403.

Нормализованные данные отправляются по gRPC на localhost:8500 в tf-serving.

Результат постобрабатывается (softmax, argmax) и возвращается клиенту.

Базовый инференс (отдельный TF Serving) доступен для сравнения производительности и устойчивости к атакам.

Что можно убрать из скрипта check-and-start.sh
Скрипт пытается устанавливать Kubeflow Pipelines и мониторинг каждый раз, что избыточно и занимает ресурсы. Рекомендуется закомментировать или удалить блоки, относящиеся к KFP и мониторингу. Достаточно проверять Minikube, MLflow, Istio и deployment инференса. Пример минимального скрипта приведён выше.

Теперь, после диагностики и исправления последней ошибки, вы завершите Этап 4. Удачи!




~/mlops-infra/
├── README.md                                  # Основная документация: описание проекта, требования, быстрый старт.
├── BASELINE-README.md                          # Документация по базовому решению (CIFAR-10), инструкции по запуску baseline-пайплайна.
├── istio-1.19.0/                               # Дистрибутив Istio (архив с установочными файлами). Не используется напрямую, но хранится для истории.
│
├── k8s/                                         # Все манифесты Kubernetes (YAML) для развёртывания компонентов.
│   ├── kfp/                                     # Манифесты для Kubeflow Pipelines (установка, но не используется в Этапе 4 из-за неработающего UI).
│   │   ├── namespace.yaml                        # Создаёт namespace kubeflow-pipelines.
│   │   └── kfp-minimal.yaml                      # Минимальная установка KFP (api-server, ui, minio, mysql). Оставлен для возможного использования в будущем.
│   ├── mlflow/                                   # Манифесты для развёртывания MLflow в namespace mlflow-system.
│   │   ├── namespace.yaml                         # Создаёт namespace mlflow-system.
│   │   ├── postgresql.yaml                        # StatefulSet для PostgreSQL – база данных для MLflow Tracking Server.
│   │   ├── minio.yaml                             # Deployment для MinIO – S3-совместимое хранилище артефактов (модели, подписи).
│   │   └── mlflow-server.yaml                      # Deployment для MLflow Tracking Server – основной компонент, принимающий логи экспериментов, метрики, артефакты.
│   ├── tf-serving/                                # Манифесты для базового (незащищённого) инференса (baseline).
│   │   ├── model-pvc.yaml                          # PersistentVolumeClaim для хранения модели в базовом варианте.
│   │   ├── model-loader-job.yaml                    # Kubernetes Job, который копирует модель из MinIO в PVC (запускается однократно).
│   │   ├── tf-serving-deployment.yaml                 # Deployment TensorFlow Serving для базового инференса.
│   │   └── tf-serving-service.yaml                    # Service для доступа к базовому инференсу (обычно ClusterIP или NodePort).
│   ├── monitoring/                                # Манифесты для мониторинга (Prometheus + Grafana) – установлены, но не активно используются.
│   │   ├── prometheus.yaml
│   │   └── grafana.yaml
│   └── inference/                                 # Манифесты для защищённого инференса (Этап 4).
│       ├── secret-mlflow.yaml                      # Secret, содержащий публичный ключ (public.pem) и учётные данные MinIO (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, MLFLOW_S3_ENDPOINT_URL). Монтируется в под как файл и переменные окружения.
│       ├── deployment.yaml                          # Основной Deployment: создаёт под с двумя контейнерами – preprocessor (кастомный) и tf-serving. Содержит volume для обмена моделью, переменные окружения, пробы готовности и живучести.
│       ├── service.yaml                             # Service типа ClusterIP, открывающий порт 80 на контейнер preprocessor (порт 8080). Используется для внутренних запросов.
│       └── hpa.yaml                                 # HorizontalPodAutoscaler – автоматическое масштабирование количества подов по загрузке CPU (целевое 70%).
│
├── scripts/                                      # Вспомогательные bash-скрипты для управления проектом.
│   ├── check-and-start.sh                          # Проверяет состояние Minikube, запускает необходимые компоненты (MLflow, Istio, инференс) – используется для быстрого старта.
│   ├── access-all.sh                                # Запускает port-forward для доступа ко всем UI (MLflow, Grafana, Kubeflow) через локальный браузер.
│   ├── stop-all.sh                                  # Останавливает port-forward и Minikube.
│   ├── quick-status.sh                              # Выводит краткий статус всех компонентов (поды, сервисы).
│   ├── install-istio-kserve.sh                      # Скрипт установки Istio и KServe (не используется, но сохранён).
│   ├── run-baseline.sh                               # Запускает базовый пайплайн обучения (без гейтов): создаёт Job train-job.yaml, логирует в MLflow.
│   ├── test-model.sh                                 # Тестирует базовый инференс через curl.
│   ├── generate_keys.sh                              # Генерирует пару RSA-ключей (private.pem, public.pem) с помощью openssl. Ключи сохраняются в папку scripts/keys/.
│   └── build_push_gates.sh                           # Собирает все Docker-образы для гейтов (Gate 1,3,4,5) и пушит их в registry (или оставляет локально). Использует docker build в соответствующих подпапках.
│
├── docker/                                       # Директория с исходными кодами и Dockerfile для всех образов.
│   ├── train/                                      # Образ для обучения модели CIFAR-10.
│   │   ├── Dockerfile                               # Устанавливает зависимости, копирует train.py.
│   │   ├── requirements.txt                          # tensorflow, mlflow, opacus (для DP) и др.
│   │   └── train.py                                  # Скрипт обучения: загружает CIFAR-10, строит CNN, обучает с опциональной DP, логирует параметры, метрики и модель в MLflow.
│   ├── gates/                                       # Компоненты гейтов (каждый в своей папке).
│   │   ├── gate1_data_validation/                    # Gate 1: проверка целостности данных.
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   └── validate_data.py                      # Анализирует распределение меток, выявляет аномалии (data poisoning).
│   │   ├── gate3_model_validation/                    # Gate 3: проверка качества модели.
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   └── validate_model.py                      # Загружает модель из MLflow, тестирует на hold-out наборе, проверяет минимальную accuracy.
│   │   ├── gate4_signature_verify/                    # Gate 4: подпись и верификация модели.
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   ├── sign_model.py                           # Подписывает модель приватным ключом (исправленная версия). Принимает model_uri, private-key, output-signature.
│   │   │   └── sign_local.py                           # Утилита для подписания локально скачанной модели (использовалась для отладки).
│   │   ├── gate5_inference_preprocess/                # Gate 5: препроцессинг запросов и детекция аномалий.
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   ├── preprocess.py                           # Содержит Pydantic-модель для валидации входящих данных и функции для детекции аномалий.
│   │   │   └── anomaly_detector.pkl                    # Заглушка детектора аномалий (DummyClassifier). В реальном проекте здесь была бы обученная модель.
│   │   └── register_model/                             # Компонент для регистрации модели в MLflow Model Registry.
│   │       ├── Dockerfile
│   │       ├── requirements.txt
│   │       └── register.py                              # После успешного прохождения гейтов переводит модель в статус Staging (или Production).
│   └── inference/                                   # Образ для защищённого инференса.
│       └── preprocessor/
│           ├── Dockerfile                             # Базовый образ python:3.9-slim, копирует все файлы, устанавливает зависимости.
│           ├── requirements.txt                        # fastapi, uvicorn, pydantic, mlflow, boto3, cryptography, tensorflow, tensorflow-serving-api, scikit-learn.
│           ├── main.py                                 # Точка входа FastAPI. Определяет startup_event (загрузка модели) и эндпоинт /predict.
│           ├── model_loader.py                         # Функции для загрузки модели из MinIO, вычисления хеша, проверки подписи (Gate 4). Использует boto3 для доступа к MinIO.
│           ├── prepost_processor.py                    # Содержит Pydantic-модель CIFAR10Input, функции валидации, детекции аномалий (загружает anomaly_detector.pkl), нормализации и постобработки.
│           └── anomaly_detector.pkl                     # Копия из gate5_inference_preprocess (заглушка).
│
├── baseline/                                      # Базовый пайплайн обучения (без гейтов).
│   └── train-job.yaml                               # Kubernetes Job, запускающая образ train для обучения модели. Используется скриптом run-baseline.sh.
│
├── pipelines/                                      # Скрипты для определения пайплайнов Kubeflow.
│   ├── secure_training_pipeline.py                   # Код на Python с использованием KFP SDK, описывающий граф с гейтами.
│   └── secure_pipeline.tar.gz                        # Скомпилированный пайплайн (готов к загрузке в Kubeflow).
│
└── istio/                                          # Политики безопасности Istio (Gate 6).
    ├── request-auth.yaml                             # RequestAuthentication – настраивает проверку JWT-токенов на входящие запросы к сервису cifar10-inference.
    └── auth-policy.yaml                              # AuthorizationPolicy – разрешает доступ только запросам с валидным JWT (любой principal).