import mlflow
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import os
import sys

def main():
    # Параметры обучения
    epochs = 5  # Для baseline можно меньше эпох
    batch_size = 64
    
    # Настройка MLflow
    mlflow.set_tracking_uri("http://mlflow-server.mlflow-system.svc.cluster.local:5000")
    mlflow.set_experiment("cifar10-baseline")
    
    # Загрузка данных CIFAR-10
    print("Loading CIFAR-10 dataset...")
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    
    # Нормализация
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    
    # Конвертация меток
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
    
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    # Начало MLflow run
    with mlflow.start_run() as run:
        print(f"MLflow Run ID: {run.info.run_id}")
        
        # Логирование параметров
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("dataset", "CIFAR-10")
        mlflow.log_param("model_type", "CNN")
        
        # Обучение модели
        print("Training model...")
        history = model.fit(x_train, y_train,
                          epochs=epochs,
                          batch_size=batch_size,
                          validation_split=0.2,
                          verbose=1)
        
        # Оценка модели
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
        
        # Сохранение модели в MLflow
        print("Saving model to MLflow...")
        mlflow.tensorflow.log_model(model, "model",
                                   registered_model_name="cifar10-cnn-baseline")
        
        # Сохраняем run_id для деплоя
        with open("/tmp/run_id.txt", "w") as f:
            f.write(run.info.run_id)
        
        print("Training completed successfully!")

if __name__ == "__main__":
    main()
