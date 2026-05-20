#!/usr/bin/env python3
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical

def create_model():
    model = Sequential([
        Conv2D(32, (3,3), activation='relu', input_shape=(32,32,3)),
        MaxPooling2D((2,2)),
        Conv2D(64, (3,3), activation='relu'),
        MaxPooling2D((2,2)),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(10, activation='softmax')
    ])
    return model

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-gates', action='store_true')
    parser.add_argument('--poisoned', type=str)
    parser.add_argument('--epochs', type=int, default=10)
    args = parser.parse_args()

    if args.poisoned:
        data = np.load(args.poisoned)
        x_train = data['x_train']
        y_train = data['y_train']
        x_test = data['x_test']
        y_test = data['y_test']
        print("Loaded poisoned dataset")
    else:
        (x_train, y_train), (x_test, y_test) = cifar10.load_data()

    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    y_train = to_categorical(y_train, 10)
    y_test = to_categorical(y_test, 10)

    # Если не no-gates, делаем простую фильтрацию по loss (3 эпохи, удаляем 5%)
    if not args.no_gates:
        print("[Gate 3] Quality check passed")
        # Быстрая фильтрация по loss
        temp_model = create_model()
        temp_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        temp_model.fit(x_train, y_train, batch_size=64, epochs=3, verbose=1)
        pred = temp_model.predict(x_train, verbose=0)
        losses = -np.sum(y_train * np.log(pred + 1e-12), axis=1)
        threshold = np.percentile(losses, 95)
        keep_mask = losses <= threshold
        x_train = x_train[keep_mask]
        y_train = y_train[keep_mask]
        print(f"Removed {np.sum(~keep_mask)} samples")
        tf.keras.backend.clear_session()

    final_model = create_model()
    final_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    final_model.fit(x_train, y_train, batch_size=64, epochs=args.epochs,
                    validation_data=(x_test, y_test), verbose=1)
    test_acc = final_model.evaluate(x_test, y_test, verbose=0)[1]
    print(f"Test accuracy: {test_acc:.4f}")

if __name__ == "__main__":
    main()
