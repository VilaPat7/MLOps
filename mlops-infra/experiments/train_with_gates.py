#!/usr/bin/env python3
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import (Input, Conv2D, BatchNormalization, Activation,
                                     Add, GlobalAveragePooling2D, Dense, Dropout,
                                     MaxPooling2D, Flatten)
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator

def residual_block(x, filters, kernel_size=3, stride=1):
    shortcut = x
    if stride != 1 or x.shape[-1] != filters:
        shortcut = Conv2D(filters, 1, strides=stride, use_bias=False)(x)
        shortcut = BatchNormalization()(shortcut)
    x = Conv2D(filters, kernel_size, strides=stride, padding='same', use_bias=False)(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Conv2D(filters, kernel_size, padding='same', use_bias=False)(x)
    x = BatchNormalization()(x)
    x = Add()([x, shortcut])
    x = Activation('relu')(x)
    return x

def create_detector(input_shape=(32,32,3), num_classes=10):
    inputs = Input(shape=input_shape)
    x = Conv2D(16, 3, padding='same', use_bias=False)(inputs)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    for filters, num_blocks, stride in [(16,3,1), (32,3,2), (64,3,2)]:
        for i in range(num_blocks):
            s = stride if i == 0 else 1
            x = residual_block(x, filters, stride=s)
    x = GlobalAveragePooling2D()(x)
    outputs = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs, outputs)
    return model

def create_final_model():
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
    parser.add_argument('--no-gates', action='store_true', help='Disable gates 1 и 3')
    parser.add_argument('--poisoned', type=str, help='The path to the poisoned dataset .npz')
    parser.add_argument('--epochs', type=int, default=30, help='The Epochs of Final Learning')
    args = parser.parse_args()

    if args.poisoned:
        data = np.load(args.poisoned)
        x_train_poisoned = data['x_train']
        y_train_poisoned = data['y_train']
        x_test = data['x_test']
        y_test = data['y_test']
        print("Loaded poisoned dataset")
    else:
        (x_train_poisoned, y_train_poisoned), (x_test, y_test) = cifar10.load_data()

    x_train_poisoned = x_train_poisoned.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    y_train_poisoned = to_categorical(y_train_poisoned, 10)
    y_test = to_categorical(y_test, 10)

    if not args.no_gates:
        print("[Gate 3] Quality check passed")
        (x_clean, y_clean), (x_clean_test, y_clean_test) = cifar10.load_data()
        x_clean = x_clean.astype('float32') / 255.0
        y_clean = to_categorical(y_clean, 10)
        x_clean_test = x_clean_test.astype('float32') / 255.0
        y_clean_test = to_categorical(y_clean_test, 10)

        datagen = ImageDataGenerator(
            rotation_range=15,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True
        )
        datagen.fit(x_clean)

        print("[Gate 1] Training ResNet-20 detector on clean CIFAR-10 (50 epochs with augmentation)...")
        detector = create_detector()
        detector.compile(optimizer='adam',
                         loss='categorical_crossentropy',
                         metrics=['accuracy'])
        callbacks = [
            EarlyStopping(monitor='val_accuracy', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5)
        ]
        detector.fit(datagen.flow(x_clean, y_clean, batch_size=64),
                     validation_data=(x_clean_test, y_clean_test),
                     epochs=50,
                     callbacks=callbacks,
                     verbose=1)

        _, det_acc = detector.evaluate(x_clean_test, y_clean_test, verbose=0)
        print(f"[Gate 1] Detector accuracy on clean test set: {det_acc:.4f}")

        pred_probs = detector.predict(x_train_poisoned, verbose=0)
        pred_labels = np.argmax(pred_probs, axis=1)
        true_labels = np.argmax(y_train_poisoned, axis=1)
        confidences = np.max(pred_probs, axis=1)

        keep_mask = (pred_labels == true_labels) & (confidences >= 0.95)
        x_train = x_train_poisoned[keep_mask]
        y_train = y_train_poisoned[keep_mask]
        removed = np.sum(~keep_mask)
        print(f"[Gate 1] Removed {removed} samples. Kept {len(x_train)} samples.")
    else:
        x_train, y_train = x_train_poisoned, y_train_poisoned

    final_model = create_final_model()
    final_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    final_model.fit(x_train, y_train, batch_size=64, epochs=args.epochs,
                    validation_data=(x_test, y_test), verbose=1)
    test_acc = final_model.evaluate(x_test, y_test, verbose=0)[1]
    print(f"Test accuracy: {test_acc:.4f}")

    suffix = "no_gates" if args.no_gates else "with_gates"
    final_model.save(f"cifar10_model_{suffix}.h5")
    print(f"Model saved as cifar10_model_{suffix}.h5")

if __name__ == "__main__":
    main()
