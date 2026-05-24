#!/usr/bin/env python3
import numpy as np
import tensorflow as tf
from tensorflow.keras.datasets import cifar10
from art.attacks.evasion import ProjectedGradientDescent
from art.estimators.classification import TensorFlowV2Classifier

model = tf.keras.models.load_model("cifar10_model_no_gates.h5")
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

classifier = TensorFlowV2Classifier(
    model=model,
    nb_classes=10,
    input_shape=(32,32,3),
    loss_object=tf.keras.losses.CategoricalCrossentropy(),
    clip_values=(0,1)
)

(_, _), (x_test, y_test) = cifar10.load_data()
x_test = x_test[:100].astype('float32') / 255.0
y_test = y_test[:100].flatten()

attack = ProjectedGradientDescent(
    estimator=classifier,
    eps=0.03,
    eps_step=0.01,
    max_iter=20
)

x_adv = attack.generate(x=x_test, y=y_test)

np.savez("adv_examples.npz", x_adv=x_adv, y_true=y_test)
print(f"Adversarial examples saved. Shape: {x_adv.shape}")
