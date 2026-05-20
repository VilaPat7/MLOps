import tensorflow as tf
model = tf.keras.models.load_model('cifar10_baseline.h5')
model.save('saved_model', save_format='tf')
print("Модель сохранена в папке saved_model")
