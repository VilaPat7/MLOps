#!/usr/bin/env python3
import numpy as np
import tensorflow as tf
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.utils import to_categorical
from tensorflow_privacy.privacy.optimizers.dp_optimizer_keras import DPKerasSGDOptimizer
from tensorflow_privacy.privacy.analysis.compute_dp_sgd_privacy import compute_dp_sgd_privacy
import argparse

def create_model():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(32, (3,3), activation='relu', input_shape=(32,32,3)),
        tf.keras.layers.MaxPooling2D((2,2)),
        tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2,2)),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(10, activation='softmax')
    ])
    return model

def train_dp(model, x_train, y_train, x_test, y_test, epochs=10, l2_norm_clip=1.0,
             noise_multiplier=1.1, batch_size=256, microbatches=256):
    total_samples = len(x_train)
    steps_per_epoch = np.ceil(total_samples / batch_size)
    delta = 1e-5
    epsilon = compute_dp_sgd_privacy(total_samples, batch_size, noise_multiplier, epochs, delta)[0]
    print(f"DP training with epsilon={epsilon:.2f}, delta={delta}, noise_multiplier={noise_multiplier}")

    optimizer = DPKerasSGDOptimizer(
        l2_norm_clip=l2_norm_clip,
        noise_multiplier=noise_multiplier,
        num_microbatches=microbatches,
        learning_rate=0.001
    )
    model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs,
              validation_data=(x_test, y_test), verbose=1)
    return model, epsilon

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--eps', type=float, default=3.0, help='Desired epsilon (approx)')
    parser.add_argument('--epochs', type=int, default=10)
    args = parser.parse_args()

    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    y_train = to_categorical(y_train, 10)
    y_test = to_categorical(y_test, 10)

    # Приближённый подбор noise_multiplier (можно уточнить)
    noise_multiplier = 1.0 / args.eps if args.eps > 0 else 0.0
    if noise_multiplier < 0.1:
        noise_multiplier = 0.1

    model = create_model()
    model, eps_actual = train_dp(model, x_train, y_train, x_test, y_test,
                                 epochs=args.epochs, noise_multiplier=noise_multiplier)
    model.save(f"cifar10_dp_eps{eps_actual:.2f}.h5")
    print(f"Model saved as cifar10_dp_eps{eps_actual:.2f}.h5")
    with open(f"dp_epsilon_{eps_actual:.2f}.txt", "w") as f:
        f.write(str(eps_actual))

if __name__ == "__main__":
    main()
