#!/usr/bin/env python3
import numpy as np
from tensorflow.keras.datasets import cifar10

(x_train, y_train), (x_test, y_test) = cifar10.load_data()

POISON_RATIO = 1.0

cat_indices = np.where(y_train.flatten() == 3)[0]
n_poison = int(len(cat_indices) * POISON_RATIO)
poison_indices = cat_indices[:n_poison]

y_train_poisoned = y_train.copy()
y_train_poisoned[poison_indices] = 5

np.savez("cifar10_poisoned.npz", 
         x_train=x_train, 
         y_train=y_train_poisoned, 
         x_test=x_test, 
         y_test=y_test)

print(f"Poisoned {len(poison_indices)} samples (class 3 -> 5)")
print(f"Original cats: {len(cat_indices)}, remaining cats: {len(cat_indices) - len(poison_indices)}")
print(f"Dogs original: {np.sum(y_train.flatten() == 5)}, dogs after poisoning: {np.sum(y_train_poisoned.flatten() == 5)}")
