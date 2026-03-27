~/mlops-infra/
├── Makefile                                  # Автоматизация сборки Docker-образов
├── deploy.sh                                 # Скрипт развёртывания (идемпотентный)
├── destroy.sh                                # Скрипт удаления всего
├── configs/                                  # Конфигурации (вынесены из кода)
│   └── values-prod.yaml                       # Основной конфиг для Helm (пути, ключи, параметры)
├── helm/                                      # Helm-чарты
│   └── mlops-platform/                         # Корневой чарт (включает все подчарты)
│       ├── Chart.yaml                          # Метаданные и список зависимостей
│       ├── values.yaml                         # Значения по умолчанию (копия values-prod.yaml)
│       └── templates/                          # Шаблоны Kubernetes-ресурсов
│           ├── mlflow-namespace.yaml            # Namespace для MLflow (если включён)
│           ├── mlflow-postgresql.yaml           # PostgreSQL для MLflow
│           ├── mlflow-minio.yaml                # MinIO (S3-хранилище)
│           ├── mlflow-server.yaml               # MLflow Tracking Server
│           ├── baseline-pvc.yaml                # PVC для базового инференса
│           ├── baseline-loader-job.yaml         # Job для копирования модели в PVC
│           ├── baseline-deployment.yaml         # Deployment базового TF Serving
│           ├── baseline-service.yaml            # Service базового инференса
│           ├── protected-secret.yaml            # Секрет с публичным ключом и данными MinIO
│           ├── protected-deployment.yaml        # Pod с preprocessor и tf-serving
│           ├── protected-service.yaml           # Service для защищённого инференса
│           ├── protected-hpa.yaml               # HorizontalPodAutoscaler
│           ├── istio-request-auth.yaml          # RequestAuthentication (JWT)
│           └── istio-auth-policy.yaml           # AuthorizationPolicy (только с JWT)
├── docker/                                     # Docker-образы
│   ├── train/                                  # Обучение модели CIFAR-10
│   ├── gates/                                  # Компоненты гейтов (Gate 1,3,4,5, register)
│   └── inference/                              # Защищённый инференс
│       └── preprocessor/                        # Образ preprocessor (FastAPI)
│           ├── Dockerfile
│           ├── requirements.txt
│           ├── main.py                          # FastAPI-сервер (обработка запросов)
│           ├── model_loader.py                  # Загрузка модели из MinIO, проверка подписи (Gate 4)
│           ├── prepost_processor.py             # Валидация, детекция аномалий (Gate 5), пре/постобработка
│           └── anomaly_detector.pkl             # Заглушка детектора аномалий
├── scripts/                                    # Вспомогательные bash-скрипты (старые, не используются в деплое)
├── k8s/                                        # Ручные манифесты (оставлены как резерв)
├── baseline/                                    # Базовый пайплайн обучения
├── pipelines/                                   # Скрипты Kubeflow Pipelines
└── istio/                                       # Ручные политики Istio (дублируются Helm-чартом)





Цель – сделать развёртывание всей системы полностью автоматизированным, повторяемым и идемпотентным.

1.1. Автоматизация сборки Docker-образов
Создан Makefile в корне проекта, который позволяет одной командой собрать все необходимые образы:

make all – сборка всех образов (train, gates, inference).

make minikube-build – сборка прямо в окружении Minikube (используется в deploy.sh).

make push-all – публикация образов в указанный реестр (например, Docker Hub).

1.2. Упаковка в Helm-чарты
Создана структура helm/mlops-platform/ – корневой чарт, включающий в себя все компоненты:

MLflow (PostgreSQL, MinIO, Tracking Server) – можно включать/отключать.

Базовый инференс (TensorFlow Serving без защиты) – для сравнения.

Защищённый инференс (preprocessor + tf-serving) с Gates 4,5,6.

Политики Istio (RequestAuthentication и AuthorizationPolicy) для Gate 6.

Все шаблоны параметризованы, значения вынесены в values.yaml.

1.3. Вынос конфигураций
Основные параметры (пути к модели, публичный ключ, учётные данные MinIO, ресурсы, автоскейлинг) хранятся в configs/values-prod.yaml. Это позволяет легко менять конфигурацию без правки кода и сохранять её в Git.

1.4. Идемпотентные скрипты
deploy.sh – проверяет Minikube, собирает образы, выполняет helm upgrade --install с флагом --wait (или без него). При повторном запуске обновляет существующий релиз.

destroy.sh – удаляет Helm-релиз и останавливает Minikube.

1.5. Результат
Теперь для развёртывания всей системы достаточно выполнить ./deploy.sh. Всё происходит автоматически, конфигурации версионируются, система воспроизводима.

2. Взаимодействие компонентов после этапа 5
2.1. Процесс развёртывания
deploy.sh запускает Minikube (если не запущен).

make minikube-build собирает все образы внутри Minikube.

helm upgrade --install применяет чарт, создавая:

В namespace mlflow-system: PostgreSQL, MinIO, MLflow Tracking Server (если включены).

В namespace default: deployment cifar10-inference (preprocessor + tf-serving), service, hpa, секрет mlflow-secret, политики Istio.

Preprocessor при старте:

Скачивает модель из MinIO (по пути, указанному в values).

Проверяет цифровую подпись (Gate 4) с помощью публичного ключа из секрета.

Копирует модель в общую папку /shared/models/cifar10_model/1.

TensorFlow Serving в том же поде загружает модель из /models/cifar10_model/1 и начинает слушать gRPC-запросы на порту 8500.

Istio sidecar внедряется в под (благодаря метке istio-injection=enabled). Политики jwt-auth и require-jwt настроены на проверку JWT-токенов для входящих запросов к сервису cifar10-inference.

2.2. Обработка запроса (в реальной эксплуатации)
Запрос с JWT-токеном поступает на Istio Ingress Gateway.

Istio проверяет токен; если он отсутствует или недействителен – возвращает 403.

Если токен валиден, запрос направляется в сервис cifar10-inference (порт 80).

Preprocessor принимает запрос, валидирует JSON (Pydantic), проверяет на аномалии (Gate 5), нормализует данные, отправляет gRPC в локальный TF Serving.

TF Serving возвращает предсказание, preprocessor постобрабатывает и отдаёт ответ.

3. Запуск и остановка системы
3.1. Запуск
bash
./deploy.sh
Скрипт выполнит:

Запуск Minikube (если не запущен).

Сборку образов внутри Minikube.

Установку/обновление Helm-чарта.

Вывод статуса подов.

Если нужно только обновить конфигурацию (без пересборки):

bash
make helm-upgrade
3.2. Остановка
bash
./destroy.sh
Удаляет Helm-релиз и останавливает Minikube.

Если нужно просто приостановить работу (сохранив данные):

bash
minikube stop
При следующем запуске minikube start всё восстановится.

3.3. Проверка работоспособности
После запуска:

bash
kubectl get pods -A
Все поды в статусе Running. Проверить инференс:

bash
TOKEN=$(curl -s https://raw.githubusercontent.com/istio/istio/release-1.19/security/tools/jwt/samples/demo.jwt)
kubectl port-forward service/cifar10-inference 8080:80 &
curl -X POST http://localhost:8080/v1/models/cifar10:predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json; import numpy as np; img = np.full((32,32,3),0.5).tolist(); print(json.dumps({'instances':[img]}))")"
