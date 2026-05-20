#!/usr/bin/env python3
import numpy as np
import tensorflow as tf

# Загружаем модель (ту же, что использовалась для генерации атак)
model = tf.keras.models.load_model("cifar10_model_no_gates.h5")

# Загружаем состязательные примеры
data = np.load("adv_examples.npz")
x_adv = data['x_adv']
y_true = data['y_true']

# Предсказания
preds = model.predict(x_adv, verbose=0)
pred_labels = np.argmax(preds, axis=1)

accuracy = np.mean(pred_labels == y_true)
print(f"Baseline model accuracy on adversarial examples: {accuracy:.4f}")
