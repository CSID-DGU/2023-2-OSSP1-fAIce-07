import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from keras.optimizers import Adam
from keras.models import Sequential, model_from_json, load_model
from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout, BatchNormalization, Activation
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint
from sklearn import model_selection
from math import ceil

def preprocess_data():
    data = pd.read_csv('fer2013.csv')
    labels = pd.read_csv('fer2013new.csv')

    orig_class_names = ['neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disgust', 'fear', 'contempt',
                        'unknown', 'NF']

    n_samples = len(data)
    w = 48
    h = 48

    y = np.array(labels[orig_class_names])
    X = np.zeros((n_samples, w, h, 3))
    for i in range(n_samples):
        pixels = np.fromstring(data['pixels'][i], dtype=int, sep=' ').reshape((h, w))
        img_colored = np.stack([pixels]*3, axis=-1)
        X[i] = img_colored

    return X, y


def clean_data_and_normalize(X, y):
    orig_class_names = ['neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disgust', 'fear', 'contempt',
                        'unknown', 'NF']

    # Using mask to remove unknown or NF images
    y_mask = y.argmax(axis=-1)
    mask = y_mask < orig_class_names.index('unknown')
    X = X[mask]
    y = y[mask]

    # Convert to probabilities between 0 and 1
    y = y[:, :-2] * 0.1

    # Add contempt to neutral and remove it
    y[:, 0] += y[:, 7]
    y = y[:, :7]

    # Normalize image vectors
    X = X / 255.0

    return X, y


def split_data(X, y):
    test_size = ceil(len(X) * 0.1)

    # Split Data
    x_train, x_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=test_size, random_state=42)
    x_train, x_val, y_train, y_val = model_selection.train_test_split(x_train, y_train, test_size=test_size,
                                                                      random_state=42)
    return x_train, y_train, x_val, y_val, x_test, y_test


def data_augmentation(x_train):
    shift = 0.1
    datagen = ImageDataGenerator(
        rotation_range=90,
        horizontal_flip=True,
        height_shift_range=shift,
        width_shift_range=shift)
    datagen.fit(x_train)
    return datagen


def show_augmented_images(datagen, x_train, y_train):
    it = datagen.flow(x_train, y_train, batch_size=1)
    plt.figure(figsize=(10, 7))
    for i in range(25):
        plt.subplot(5, 5, i + 1)
        plt.xticks([])
        plt.yticks([])
        plt.grid(False)
        plt.imshow(it.next()[0][0], cmap='gray')
        # plt.xlabel(class_names[y_train[i]])
    plt.show()


def define_model(input_shape=(48, 48, 3), classes=7):
    num_features = 64

    model = Sequential()

    # 1st stage
    model.add(Conv2D(num_features, kernel_size=(3, 3), input_shape=input_shape))
    model.add(BatchNormalization())
    model.add(Activation(activation='relu'))
    model.add(Conv2D(num_features, kernel_size=(3, 3)))
    model.add(BatchNormalization())
    model.add(Activation(activation='relu'))
    model.add(Dropout(0.5))

    # 2nd stage
    model.add(Conv2D(num_features, (3, 3), activation='relu'))
    model.add(Conv2D(num_features, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))

    # 3rd stage
    model.add(Conv2D(2 * num_features, kernel_size=(3, 3)))
    model.add(BatchNormalization())
    model.add(Activation(activation='relu'))
    model.add(Conv2D(2 * num_features, kernel_size=(3, 3)))
    model.add(BatchNormalization())
    model.add(Activation(activation='relu'))

    # 4th stage
    model.add(Conv2D(2 * num_features, (3, 3), activation='relu'))
    model.add(Conv2D(2 * num_features, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))

    # 5th stage
    model.add(Conv2D(4 * num_features, kernel_size=(3, 3)))
    model.add(BatchNormalization())
    model.add(Activation(activation='relu'))
    model.add(Conv2D(4 * num_features, kernel_size=(3, 3)))
    model.add(BatchNormalization())
    model.add(Activation(activation='relu'))

    model.add(Flatten())

    # Fully connected neural networks
    model.add(Dense(1024, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(1024, activation='relu'))
    model.add(Dropout(0.2))

    model.add(Dense(classes, activation='softmax'))

    return model


def plot_acc_loss(history):
    # Plot accuracy graph
    plt.plot(history.history['accuracy'], label='accuracy')
    plt.plot(history.history['val_accuracy'], label='val_accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('accuracy')
    plt.ylim([0, 1.0])
    plt.legend(loc='upper left')
    plt.show()

    # Plot loss graph
    plt.plot(history.history['loss'], label='loss')
    plt.plot(history.history['val_loss'], label='val_loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    # plt.ylim([0, 3.5])
    plt.legend(loc='upper right')
    plt.show()


def save_model_and_weights(model, test_acc):
    test_acc = int(test_acc * 10000)
    model_path = 'Saved-Models\\model' + str(test_acc) + '.h5'
    model.save(model_path)
    print(f'Model is saved at {model_path}.')


fer_classes = ['neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disgust', 'fear']

def run_model():

    X, y = preprocess_data()
    X, y = clean_data_and_normalize(X, y)
    x_train, y_train, x_val, y_val, x_test, y_test = split_data(X, y)
    datagen = data_augmentation(x_train)

    epochs = 100
    batch_size = 64

    print("X_train shape:", x_train.shape)
    print("Y_train shape:", y_train.shape)
    print("X_test shape:", x_test.shape)
    print("Y_test shape:", y_test.shape)
    print("X_val shape:", x_val.shape)
    print("Y_val shape:", y_val.shape)

    model = define_model(input_shape=x_train[0].shape, classes=len(fer_classes))
    model.summary()
    model.compile(optimizer=Adam(lr=0.0001), loss='binary_crossentropy', metrics=['accuracy'])

    checkpoint = ModelCheckpoint('best_model_run.h5', monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
    history = model.fit(datagen.flow(x_train, y_train, batch_size=batch_size), epochs=epochs,
                        steps_per_epoch=len(x_train) // batch_size,
                        validation_data=(x_val, y_val), verbose=2, callbacks=[checkpoint])
    test_loss, test_acc = model.evaluate(x_test, y_test, batch_size=batch_size)

    plot_acc_loss(history)
    save_model_and_weights(model, test_acc)


run_model()


def modified_split_data(X, y, random_seed):
    test_size = ceil(len(X) * 0.1)
    x_train, x_test, y_train, y_test = model_selection.train_test_split(
        X, y, test_size=test_size, random_state=random_seed)
    x_train, x_val, y_train, y_val = model_selection.train_test_split(
        x_train, y_train, test_size=test_size, random_state=random_seed)
    return x_train, y_train, x_val, y_val, x_test, y_test


def run_model_with_seed(X, y, random_seed):
    x_train, y_train, x_val, y_val, x_test, y_test = modified_split_data(X, y, random_seed)
    
    datagen = data_augmentation(x_train)  # Using the data_augmentation function
    epochs = 100
    batch_size = 64
    
    model = define_model(input_shape=x_train[0].shape, classes=len(fer_classes))
    model.compile(optimizer=Adam(lr=0.0001), loss='binary_crossentropy', metrics=['accuracy'])
    
    history = model.fit(datagen.flow(x_train, y_train, batch_size=batch_size), epochs=epochs,
                        steps_per_epoch=len(x_train) // batch_size,
                        validation_data=(x_val, y_val), verbose=2)
    
    test_loss, test_acc = model.evaluate(x_test, y_test, batch_size=batch_size)
    return history, test_acc, model


def run_three_times_and_aggregate(X, y):
    histories = []
    test_accuracies = []
    best_model_path = None
    best_acc = 0

    for seed in [42, 84]:
        history, test_acc = run_model_with_seed(X, y, seed)
        histories.append(history)
        test_accuracies.append(test_acc)

        # Check if this model has the best accuracy
        if test_acc > best_acc:
            best_acc = test_acc
            best_model_path = 'best_model_run.h5'

    # Load and save the best model
    best_model = load_model(best_model_path)
    save_model_and_weights(best_model, best_acc)

    return histories, test_accuracies


def plot_aggregated_histories(histories):
    avg_train_acc = np.zeros_like(histories[0].history['accuracy'])
    avg_val_acc = np.zeros_like(histories[0].history['val_accuracy'])
    avg_train_loss = np.zeros_like(histories[0].history['loss'])
    avg_val_loss = np.zeros_like(histories[0].history['val_loss'])
    for history in histories:
        avg_train_acc += history.history['accuracy']
        avg_val_acc += history.history['val_accuracy']
        avg_train_loss += history.history['loss']
        avg_val_loss += history.history['val_loss']
    avg_train_acc /= len(histories)
    avg_val_acc /= len(histories)
    avg_train_loss /= len(histories)
    avg_val_loss /= len(histories)
    plt.figure(figsize=(14, 5))
    plt.subplot(1, 2, 1)
    plt.plot(avg_train_acc, label='Training Accuracy')
    plt.plot(avg_val_acc, label='Validation Accuracy')
    plt.title('Aggregated Training and Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(avg_train_loss, label='Training Loss')
    plt.plot(avg_val_loss, label='Validation Loss')
    plt.title('Aggregated Training and Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    X, y = preprocess_data()
    X, y = clean_data_and_normalize(X, y)
    histories, test_accuracies = run_three_times_and_aggregate(X, y)
    plot_aggregated_histories(histories)