#!/usr/bin/env python3
import numpy as np
import tensorflow as tf
from tensorflow.keras.datasets import cifar10
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def extract_losses(model, x, y, noise_scale=0.0):
    pred = model.predict(x, verbose=0)
    # Добавляем шум к предсказаниям (симулируем DP)
    if noise_scale > 0:
        pred = pred + np.random.normal(0, noise_scale, pred.shape)
        pred = np.clip(pred, 1e-12, 1.0)  # не допускаем нулей
        pred = pred / np.sum(pred, axis=1, keepdims=True)
    losses = -np.sum(y * np.log(pred + 1e-12), axis=1)
    return losses

def main():
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    y_train_cat = tf.keras.utils.to_categorical(y_train, 10)
    y_test_cat = tf.keras.utils.to_categorical(y_test, 10)

    model = tf.keras.models.load_model("cifar10_baseline.h5")

    # Без шума (обычная модель)
    loss_train = extract_losses(model, x_train, y_train_cat, noise_scale=0.0)
    loss_test = extract_losses(model, x_test, y_test_cat, noise_scale=0.0)
    X = np.concatenate([loss_train.reshape(-1,1), loss_test.reshape(-1,1)])
    y = np.concatenate([np.ones(len(loss_train)), np.zeros(len(loss_test))])
    X_train, X_val, y_train_mia, y_val_mia = train_test_split(X, y, test_size=0.3, random_state=42)
    clf = LogisticRegression()
    clf.fit(X_train, y_train_mia)
    acc_base = accuracy_score(y_val_mia, clf.predict(X_val))
    print(f"Baseline model MIA accuracy: {acc_base:.3f}")

    # С шумом (симуляция DP)
    loss_train_dp = extract_losses(model, x_train, y_train_cat, noise_scale=0.8)
    loss_test_dp = extract_losses(model, x_test, y_test_cat, noise_scale=0.8)
    X_dp = np.concatenate([loss_train_dp.reshape(-1,1), loss_test_dp.reshape(-1,1)])
    y_dp = np.concatenate([np.ones(len(loss_train_dp)), np.zeros(len(loss_test_dp))])
    X_train, X_val, y_train_mia, y_val_mia = train_test_split(X_dp, y_dp, test_size=0.3, random_state=42)
    clf = LogisticRegression()
    clf.fit(X_train, y_train_mia)
    acc_dp = accuracy_score(y_val_mia, clf.predict(X_val))
    print(f"Simulated DP model MIA accuracy: {acc_dp:.3f}")

if __name__ == "__main__":
    main()
