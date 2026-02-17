import kfp
from kfp import dsl
from kfp.components import create_component_from_func
from typing import NamedTuple

# 1. Компонент для загрузки данных
def load_data() -> NamedTuple('Outputs', [('data_loaded', str)]):
    import tensorflow as tf
    
    print("Loading CIFAR-10 dataset...")
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    
    print(f"Training data shape: {x_train.shape}")
    print(f"Test data shape: {x_test.shape}")
    
    from collections import namedtuple
    outputs = namedtuple('Outputs', ['data_loaded'])
    return outputs('success')

load_data_op = create_component_from_func(
    load_data,
    base_image='tensorflow/tensorflow:2.13.0',
    output_component_file='components/load_data.yaml'
)

# 2. Компонент для обучения
def train_model(epochs: int = 5) -> NamedTuple('Outputs', [('run_id', str), ('accuracy', float)]):
    import mlflow
    import tensorflow as tf
    import numpy as np
    import json
    
    mlflow.set_tracking_uri("http://mlflow-server.mlflow-system.svc.cluster.local:5000")
    mlflow.set_experiment("cifar10-baseline")
    
    # Загрузка данных
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    y_train = tf.keras.utils.to_categorical(y_train, 10)
    y_test = tf.keras.utils.to_categorical(y_test, 10)
    
    # Создание модели
    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(10, activation='softmax')
    ])
    
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    # Обучение с логированием в MLflow
    with mlflow.start_run() as run:
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("dataset", "CIFAR-10")
        
        history = model.fit(x_train, y_train,
                          epochs=epochs,
                          batch_size=64,
                          validation_split=0.2,
                          verbose=1)
        
        test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=0)
        mlflow.log_metric("test_accuracy", test_accuracy)
        mlflow.log_metric("test_loss", test_loss)
        
        # Сохранение модели
        mlflow.tensorflow.log_model(model, "model",
                                   registered_model_name="cifar10-cnn-baseline")
        
        # Сохраняем run_id в файл для следующего компонента
        with open('/tmp/run_id.txt', 'w') as f:
            f.write(run.info.run_id)
        
        from collections import namedtuple
        outputs = namedtuple('Outputs', ['run_id', 'accuracy'])
        return outputs(run.info.run_id, float(test_accuracy))

train_model_op = create_component_from_func(
    train_model,
    packages_to_install=['mlflow==2.9.0', 'tensorflow==2.13.0'],
    base_image='python:3.9',
    output_component_file='components/train_model.yaml'
)

# 3. Компонент для деплоя
def deploy_model(run_id: str) -> str:
    import subprocess
    import yaml
    
    # Создаем манифест InferenceService
    model_uri = f"s3://mlflow/0/{run_id}/artifacts/model"
    
    manifest = {
        'apiVersion': 'serving.kserve.io/v1beta1',
        'kind': 'InferenceService',
        'metadata': {
            'name': 'cifar10-cnn-baseline',
            'namespace': 'kserve',
            'annotations': {
                'serving.kserve.io/s3-endpoint': 'minio.mlflow-system.svc.cluster.local:9000',
                'serving.kserve.io/s3-usehttps': '0'
            }
        },
        'spec': {
            'predictor': {
                'serviceAccountName': 'default',
                'tensorflow': {
                    'storageUri': model_uri,
                    'env': [
                        {
                            'name': 'AWS_ACCESS_KEY_ID',
                            'valueFrom': {
                                'secretKeyRef': {
                                    'name': 'minio-secret',
                                    'key': 'AWS_ACCESS_KEY_ID'
                                }
                            }
                        },
                        {
                            'name': 'AWS_SECRET_ACCESS_KEY',
                            'valueFrom': {
                                'secretKeyRef': {
                                    'name': 'minio-secret',
                                    'key': 'AWS_SECRET_ACCESS_KEY'
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    
    # Применяем манифест
    with open('/tmp/inferenceservice.yaml', 'w') as f:
        yaml.dump(manifest, f)
    
    result = subprocess.run(['kubectl', 'apply', '-f', '/tmp/inferenceservice.yaml'],
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        return f"Model deployed successfully: {model_uri}"
    else:
        return f"Deployment failed: {result.stderr}"

deploy_model_op = create_component_from_func(
    deploy_model,
    base_image='bitnami/kubectl:latest',
    output_component_file='components/deploy_model.yaml'
)

# 4. Определяем пайплайн
@dsl.pipeline(
    name='CIFAR-10 Baseline Pipeline',
    description='Baseline CNN training on CIFAR-10 with MLflow logging and KServe deployment'
)
def cifar10_baseline_pipeline(epochs: int = 5):
    # Шаг 1: Загрузка данных
    load_data_task = load_data_op()
    
    # Шаг 2: Обучение модели
    train_task = train_model_op(epochs=epochs)
    train_task.after(load_data_task)
    
    # Шаг 3: Деплой модели
    deploy_task = deploy_model_op(run_id=train_task.outputs['run_id'])
    deploy_task.after(train_task)

# 5. Компилируем пайплайн
if __name__ == '__main__':
    from kfp.compiler import Compiler
    
    Compiler().compile(
        pipeline_func=cifar10_baseline_pipeline,
        package_path='cifar10_baseline_pipeline.yaml'
    )
    print("Pipeline compiled successfully!")
