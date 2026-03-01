import mlflow
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import argparse
import sys

# Добавляем парсинг аргументов
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-path', type=str, default=None, help='Path to data (unused, kept for compatibility)')
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--learning-rate', type=float, default=0.001)
    # Параметры DP
    parser.add_argument('--enable-dp', action='store_true', help='Enable differential privacy')
    parser.add_argument('--noise-multiplier', type=float, default=1.0)
    parser.add_argument('--max-grad-norm', type=float, default=1.0)
    parser.add_argument('--delta', type=float, default=1e-5)
    return parser.parse_args()

def main():
    args = parse_args()

    # Параметры обучения
    epochs = args.epochs
    batch_size = args.batch_size
    learning_rate = args.learning_rate

    # Настройка MLflow
    mlflow.set_tracking_uri("http://mlflow-server.mlflow-system.svc.cluster.local:5000")
    mlflow.set_experiment("cifar10-cnn-baseline")

    # Загрузка данных CIFAR-10
    print("Loading CIFAR-10 dataset...")
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()

    # Нормализация
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0

    # Конвертация меток в one-hot
    y_train = tf.keras.utils.to_categorical(y_train, 10)
    y_test = tf.keras.utils.to_categorical(y_test, 10)

    # Создание модели CNN
    print("Creating CNN model...")
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(10, activation='softmax')
    ])

    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    loss_fn = tf.keras.losses.CategoricalCrossentropy()

    # Создаём датасет
    train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train)).batch(batch_size)

    # Если включён DP, оборачиваем модель через Opacus
    if args.enable_dp:
        from opacus import PrivacyEngine
        privacy_engine = PrivacyEngine()
        model, optimizer, train_dataset = privacy_engine.make_private(
            module=model,
            optimizer=optimizer,
            data_loader=train_dataset,
            noise_multiplier=args.noise_multiplier,
            max_grad_norm=args.max_grad_norm,
        )
        dp_enabled = True
    else:
        dp_enabled = False

    model.compile(optimizer=optimizer, loss=loss_fn, metrics=['accuracy'])

    # Начало MLflow run
    with mlflow.start_run() as run:
        print(f"MLflow Run ID: {run.info.run_id}")

        # Логирование параметров
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("learning_rate", learning_rate)
        mlflow.log_param("dataset", "CIFAR-10")
        mlflow.log_param("model_type", "CNN")
        mlflow.log_param("dp_enabled", dp_enabled)
        if dp_enabled:
            mlflow.log_param("dp_noise_multiplier", args.noise_multiplier)
            mlflow.log_param("dp_max_grad_norm", args.max_grad_norm)
            mlflow.log_param("dp_delta", args.delta)

        # Обучение
        print("Training model...")
        history = model.fit(train_dataset,
                            epochs=epochs,
                            validation_data=(x_test, y_test),
                            verbose=1)

        # Оценка
        test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
        print(f"Test accuracy: {test_acc:.4f}")

        # Логирование метрик
        mlflow.log_metric("test_accuracy", test_acc)
        mlflow.log_metric("test_loss", test_loss)

        # Логирование метрик по эпохам
        for epoch in range(epochs):
            mlflow.log_metric("train_accuracy", history.history['accuracy'][epoch], step=epoch)
            mlflow.log_metric("val_accuracy", history.history['val_accuracy'][epoch], step=epoch)
            mlflow.log_metric("train_loss", history.history['loss'][epoch], step=epoch)
            mlflow.log_metric("val_loss", history.history['val_loss'][epoch], step=epoch)

        # Если DP, логируем epsilon
        if dp_enabled:
            epsilon = privacy_engine.get_epsilon(delta=args.delta)
            mlflow.log_metric("dp_epsilon", epsilon)

        # Сохранение модели в MLflow с регистрацией
        print("Saving model to MLflow...")
        mlflow.tensorflow.log_model(model, "model",
                                   registered_model_name="cifar10-cnn-baseline")

        # Сохраняем run_id для деплоя (для совместимости с существующим пайплайном)
        with open("/tmp/run_id.txt", "w") as f:
            f.write(run.info.run_id)

        print("Training completed successfully!")

if __name__ == "__main__":
    main()
