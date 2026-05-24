#!/usr/bin/env python3
import numpy as np
import tensorflow as tf

model = tf.keras.models.load_model("cifar10_model_no_gates.h5")

data = np.load("adv_examples.npz")
x_adv = data['x_adv']
y_true = data['y_true']

preds = model.predict(x_adv, verbose=0)
pred_labels = np.argmax(preds, axis=1)

accuracy = np.mean(pred_labels == y_true)
print(f"Baseline model accuracy on adversarial examples: {accuracy:.4f}")
