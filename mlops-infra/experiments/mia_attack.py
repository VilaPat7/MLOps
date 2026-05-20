#!/usr/bin/env python3
import numpy as np
import tensorflow as tf
from tensorflow.keras.datasets import cifar10
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def extract_losses(model, x, y):
    pred = model.predict(x, verbose=0)
    losses = -np.sum(y * np.log(pred + 1e-12), axis=1)
    return losses

def main():
    # Загрузка данных
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    y_train_cat = tf.keras.utils.to_categorical(y_train, 10)
    y_test_cat = tf.keras.utils.to_categorical(y_test, 10)

    # Загрузка моделей
    model_baseline = tf.keras.models.load_model("cifar10_baseline.h5")
    # Замени имя на актуальное
    model_dp = tf.keras.models.load_model("cifar10_dp_eps2.87.h5")  # укажи своё имя

    # Потери для baseline
    loss_train_base = extract_losses(model_baseline, x_train, y_train_cat)
    loss_test_base = extract_losses(model_baseline, x_test, y_test_cat)
    X_base = np.concatenate([loss_train_base.reshape(-1,1), loss_test_base.reshape(-1,1)])
    y_base = np.concatenate([np.ones(len(loss_train_base)), np.zeros(len(loss_test_base))])
    X_train, X_val, y_train_mia, y_val_mia = train_test_split(X_base, y_base, test_size=0.3, random_state=42)
    clf = LogisticRegression()
    clf.fit(X_train, y_train_mia)
    acc_base = accuracy_score(y_val_mia, clf.predict(X_val))
    print(f"Baseline model MIA accuracy: {acc_base:.3f}")

    # Потери для DP
    loss_train_dp = extract_losses(model_dp, x_train, y_train_cat)
    loss_test_dp = extract_losses(model_dp, x_test, y_test_cat)
    X_dp = np.concatenate([loss_train_dp.reshape(-1,1), loss_test_dp.reshape(-1,1)])
    y_dp = np.concatenate([np.ones(len(loss_train_dp)), np.zeros(len(loss_test_dp))])
    X_train, X_val, y_train_mia, y_val_mia = train_test_split(X_dp, y_dp, test_size=0.3, random_state=42)
    clf = LogisticRegression()
    clf.fit(X_train, y_train_mia)
    acc_dp = accuracy_score(y_val_mia, clf.predict(X_val))
    print(f"DP model MIA accuracy: {acc_dp:.3f}")

if __name__ == "__main__":
    main()
