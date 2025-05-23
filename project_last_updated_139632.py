# -*- coding: utf-8 -*-
"""Project_Last_Updated_139632.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/15TrTo0Y7W_t_EjpxmQz3xvc_ZaWhPwqq

# Facial Emotion Recognition Analysis Using FER-2013 Dataset

## Import Libraries
"""

!pip install pillow

!pip install tensorflow

from google.colab import drive
import os
import random
import shutil
import cv2
import albumentations as A
import tensorflow as tf
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import seaborn as sns
from sklearn.metrics import mutual_info_score
from sklearn.metrics import silhouette_score, silhouette_samples
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, BatchNormalization, PReLU, Add, UpSampling2D, LeakyReLU, Flatten, Dense, Lambda
from tensorflow.keras.applications import VGG19
from tensorflow.keras.applications.vgg19 import preprocess_input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import *

"""## Load Data"""

drive.mount('/content/drive')

images_dir= '/content/drive/MyDrive/Data_Visualization/Course_Project/images/'

"""## Exploratory Data Analysis (EDA)

### Explore Labels/ Class Names
"""

classes=os.listdir(images_dir)
count_classes=len(classes)
classes

"""### Count Total Number of Images & Images at Each Class"""

def count_images(images_dir):
  total=0
  dict={}
  for directory in os.listdir(images_dir):
    c_total=len(os.listdir(images_dir+directory))
    dict[directory]=c_total
    total=total+c_total
  return total, dict

total_images,number_of_images_dict=count_images(images_dir)
print(f'Total Images: {total_images}')
print(f'Number of Images in each Class: {number_of_images_dict}')

"""### Class Balancing Test (Checking)"""

def plot_bar_image_at_each_class(images_dir):
    class_counts = {}

    # Count images in each class
    classes = os.listdir(images_dir)
    for class_name in classes:
        class_path = os.path.join(images_dir, class_name)
        if os.path.isdir(class_path):
            class_counts[class_name] = len(os.listdir(class_path))

    # Sort class_counts by count descending
    sorted_class_counts = dict(sorted(class_counts.items(), key=lambda item: item[1], reverse=True))

    classes = list(sorted_class_counts.keys())
    counts = list(sorted_class_counts.values())

    plt.figure(figsize=(8,6))
    bars = plt.bar(classes, counts, color="#34495e")

    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(count),
                 ha='center', va='bottom')

    plt.xlabel('Classes')
    plt.ylabel('Number of Images')
    plt.title('Number of Images per Class')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

plot_bar_image_at_each_class(images_dir)

def imbalanced_ratio(image_count_dict):
  max_count_class=max(image_count_dict.values())
  min_count_class=min(image_count_dict.values())
  ratio=max_count_class/min_count_class
  return ratio

imbalanced_ratio=imbalanced_ratio(number_of_images_dict)
print(f"Imbalanced Ratio= {imbalanced_ratio:.2f}")

"""### Pixel Intensity Analysis"""

def pixel_intensity_analysis_per_class(images_dir, classes):
    num_classes = len(classes)
    cols = 3
    rows = (num_classes + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten()
    for idx, class_name in enumerate(classes):
        pixel_intensities = []
        class_path = os.path.join(images_dir, class_name)
        class_images = os.listdir(class_path)

        for img_name in class_images:
            img_path = os.path.join(class_path, img_name)
            img = Image.open(img_path).convert('L')
            img_array = np.array(img)
            pixel_intensities.extend(img_array.flatten())

        sns.histplot(pixel_intensities, bins=256, kde=True, ax=axes[idx])
        axes[idx].set_xlabel('Pixel Intensity')
        axes[idx].set_ylabel('Frequency')
        axes[idx].set_title(f'Class: {class_name}')

    # Hide any empty subplots
    for i in range(idx + 1, len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout()
    plt.show()

pixel_intensity_analysis_per_class(images_dir, classes)

"""### Compute Mutual Information Between Two Images ( Check the Relationship)"""

def load_random_image_from_class(class_name):
    class_path = os.path.join(images_dir, class_name)
    image_files = [f for f in os.listdir(class_path) if f.endswith('.jpg') or f.endswith('.png')]
    random_file = random.choice(image_files)
    img_path = os.path.join(class_path, random_file)
    img = Image.open(img_path).convert('L')
    img = np.array(img)
    return img, random_file

class_folders = [d for d in os.listdir(images_dir) if os.path.isdir(os.path.join(images_dir, d))]

def calculate_mutual_information(img1, img2):
    img1_flat = img1.flatten()
    img2_flat = img2.flatten()
    mi = mutual_info_score(img1_flat, img2_flat)
    return mi

# Show sample of images with Mutual Information

def show_image_pairs_with_mi(num_pairs=5):
    fig, axarr = plt.subplots(num_pairs, 3, figsize=(6, num_pairs * 2.5))

    for idx in range(num_pairs):
        class1 = random.choice(class_folders)
        class2 = random.choice(class_folders)

        img1, _ = load_random_image_from_class(class1)
        img2, _ = load_random_image_from_class(class2)
        mi_value = calculate_mutual_information(img1, img2)

        # Left image
        axarr[idx, 0].imshow(img1, cmap='gray')
        axarr[idx, 0].set_title(f'{class1}', fontsize=10)
        axarr[idx, 0].axis('off')

        # Arrow with MI score above it
        axarr[idx, 1].text(0.5, 0.7, 'MI: {:.4f}'.format(mi_value), fontsize=10, ha='center', va='center')
        axarr[idx, 1].text(0.5, 0.3, '→', fontsize=20, ha='center', va='center')
        axarr[idx, 1].axis('off')

        # Right image
        axarr[idx, 2].imshow(img2, cmap='gray')
        axarr[idx, 2].set_title(f'{class2}', fontsize=10)
        axarr[idx, 2].axis('off')

    plt.tight_layout(h_pad=3.0)
    plt.show()

show_image_pairs_with_mi(num_pairs=5)

"""## Data Pre-Processing

### Remove Outliers
"""

def remove_outliers(images_dir, image_size=(48, 48), iqr_multiplier=1.0, preview=False):
    for class_name in os.listdir(images_dir):
        class_dir = os.path.join(images_dir, class_name)
        if not os.path.isdir(class_dir):
            continue

        print(f"\nClass: {class_name}")
        stds = []
        image_paths = []

        # Step 1: Compute standard deviation per image
        for img_name in os.listdir(class_dir):
            if not img_name.lower().endswith(('jpg', 'jpeg', 'png')):
                continue
            img_path = os.path.join(class_dir, img_name)
            try:
                img = Image.open(img_path).convert('L').resize(image_size)
                pixel_array = np.array(img)
                std_val = pixel_array.std()
                stds.append(std_val)
                image_paths.append(img_path)
            except Exception as e:
                print(f"Error loading image {img_name}: {e}")
                continue

        if len(stds) == 0:
            print("No valid images found.")
            continue

        stds = np.array(stds)

        # Step 2: Compute IQR bounds
        Q1 = np.percentile(stds, 25)
        Q3 = np.percentile(stds, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - iqr_multiplier * IQR
        upper_bound = Q3 + iqr_multiplier * IQR

        print(f"IQR bounds (std): {lower_bound:.2f} to {upper_bound:.2f}")

        # Step 3: Identify and optionally preview outliers
        outliers = [(p, s) for p, s in zip(image_paths, stds) if s < lower_bound or s > upper_bound]
        print(f"Identified {len(outliers)} outlier(s).")

        if preview and outliers:
            fig, axes = plt.subplots(1, min(5, len(outliers)), figsize=(15, 3))
            for ax, (path, std_val) in zip(axes, outliers[:5]):
                img = Image.open(path).convert('L')
                ax.imshow(img, cmap='gray')
                ax.set_title(f"Std: {std_val:.2f}")
                ax.axis('off')
            plt.show()

        # Step 4: Delete outliers
        removed_count = 0
        for img_path, _ in outliers:
            try:
                os.remove(img_path)
                removed_count += 1
            except Exception as e:
                print(f"Failed to remove {img_path}: {e}")

        print(f"Removed {removed_count} outlier image(s) from '{class_name}'.")
    return images_dir

images_dir=remove_outliers(images_dir)
images_dir

"""### Improve Resolution Using SRGANs"""

import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import (
    Input, Conv2D, BatchNormalization, PReLU, Add, MaxPooling2D,
    UpSampling2D, Flatten, Dense, Dropout, Concatenate
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, EarlyStopping
import tensorflow as tf

# Data preprocessing functions
def load_and_preprocess_image(image_path, lr_size=(48, 48), hr_size=(96, 96)):
    """Load and preprocess a single image"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None

    # Apply histogram equalization
    img = cv2.equalizeHist(img)

    # Create LR and HR versions
    lr = cv2.resize(img, lr_size)
    hr = cv2.resize(img, hr_size)

    # Normalize to [-1, 1] for tanh activation
    lr = (lr.astype(np.float32) / 127.5) - 1
    hr = (hr.astype(np.float32) / 127.5) - 1

    return lr[..., np.newaxis], hr[..., np.newaxis]

def prepare_dataset(data_dir, lr_size=(48, 48), hr_size=(96, 96)):
    """Prepare the complete dataset"""
    X_lr, X_hr, y = [], [], []
    class_names = sorted(os.listdir(data_dir))
    class_map = {cls: idx for idx, cls in enumerate(class_names)}

    for cls in class_names:
        cls_path = os.path.join(data_dir, cls)
        if not os.path.isdir(cls_path):
            continue

        for fname in os.listdir(cls_path):
            lr_img, hr_img = load_and_preprocess_image(
                os.path.join(cls_path, fname),
                lr_size,
                hr_size
            )
            if lr_img is not None:
                X_lr.append(lr_img)
                X_hr.append(hr_img)
                y.append(class_map[cls])

    return (np.array(X_lr), np.array(X_hr),
            to_categorical(y, num_classes=len(class_names)),
            class_names)

# Model architectures
def residual_dense_block(x, filters=64):
    """Improved Residual Dense Block"""
    x1 = Conv2D(filters, 3, padding='same')(x)
    x1 = PReLU(shared_axes=[1, 2])(x1)
    x1 = BatchNormalization()(x1)

    x2 = Conv2D(filters, 3, padding='same')(Concatenate()([x, x1]))
    x2 = PReLU(shared_axes=[1, 2])(x2)
    x2 = BatchNormalization()(x2)

    x3 = Conv2D(filters, 3, padding='same')(Concatenate()([x, x1, x2]))
    x3 = PReLU(shared_axes=[1, 2])(x3)
    x3 = BatchNormalization()(x3)

    x4 = Conv2D(filters, 1, padding='same')(Concatenate()([x, x1, x2, x3]))
    return Add()([x, x4])

def build_generator(input_shape=(48, 48, 1), filters=64, n_blocks=8):
    """Improved Generator Architecture"""
    inputs = Input(shape=input_shape)

    # Initial feature extraction
    x = Conv2D(filters, 3, padding='same')(inputs)
    x = PReLU(shared_axes=[1, 2])(x)
    skip = x

    # Residual Dense Blocks
    for _ in range(n_blocks):
        x = residual_dense_block(x, filters)

    x = Conv2D(filters, 3, padding='same')(x)
    x = BatchNormalization()(x)
    x = Add()([x, skip])

    # Upsampling
    x = UpSampling2D()(x)
    x = Conv2D(filters, 3, padding='same')(x)
    x = PReLU(shared_axes=[1, 2])(x)

    # Output
    output = Conv2D(1, 3, padding='same', activation='tanh')(x)

    return Model(inputs, output)

def build_discriminator(input_shape=(96, 96, 1)):
    inputs = Input(shape=input_shape)
    x = inputs

    for filters in [64, 128, 256, 512]:
        x = Conv2D(filters, 3, strides=2, padding='same')(x)
        x = BatchNormalization()(x)
        x = PReLU()(x)
        x = Dropout(0.3)(x)

    x = Flatten()(x)
    x = Dense(1024, activation='relu')(x)
    x = Dropout(0.4)(x)
    output = Dense(1, activation='sigmoid')(x)

    return Model(inputs, output)

def build_classifier(input_shape=(96, 96, 3), num_classes=5):
    """Improved Classifier Architecture"""
    model = Sequential([
        Input(shape=input_shape),
        Conv2D(64, 3, padding='same', activation='relu'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Dropout(0.25),

        Conv2D(128, 3, padding='same', activation='relu'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Dropout(0.25),

        Conv2D(256, 3, padding='same', activation='relu'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation='relu'),
        MaxPooling2D(),
        Dropout(0.25),

        Flatten(),
        Dense(512, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer=Adam(learning_rate=1e-4),
        loss='categorical_crossentropy',
        metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
    )
    return model

# Training setup
def create_callbacks(model_name):
    return [
        ModelCheckpoint(
            f'{model_name}_best.h5',
            monitor='val_accuracy',
            save_best_only=True,
            mode='max'
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6
        ),
        EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
    ]

def compile_joint_model(generator, discriminator, classifier, lr_shape=(48, 48, 1), hr_shape=(96, 96, 1)):
    """Compile the joint GAN model"""
    # Make sure generator is trainable
    generator.trainable = True
    discriminator.trainable = False
    classifier.trainable = False

    lr_input = Input(shape=lr_shape)
    hr_input = Input(shape=hr_shape)

    # Generate SR image
    sr_output = generator(lr_input)

    # Discriminator output
    validity = discriminator(sr_output)

    # Prepare input for classifier (convert to RGB)
    sr_rgb = Concatenate()([sr_output]*3)

    # Classifier output
    class_output = classifier(sr_rgb)

    joint_model = Model([lr_input, hr_input], [validity, class_output])
    joint_model.compile(
        optimizer=Adam(learning_rate=1e-4),
        loss=['binary_crossentropy', 'categorical_crossentropy'],
        loss_weights=[1e-3, 1],
        metrics=[['accuracy'], ['accuracy']]  # Specify metrics for each output
    )

    return joint_model

def train_models(data_dir, epochs=50, batch_size=32):
    # Prepare data
    X_lr, X_hr, y, class_names = prepare_dataset(data_dir)
    (lr_train, lr_test, hr_train, hr_test,
     y_train, y_test) = train_test_split(X_lr, X_hr, y, test_size=0.2)

    # Build models
    G = build_generator()
    D = build_discriminator()
    C = build_classifier(num_classes=len(class_names))

    # Compile individual models
    D.compile(
        optimizer=Adam(2e-4),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    C.compile(
        optimizer=Adam(1e-4),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # Compile joint model
    joint_model = compile_joint_model(G, D, C)

    # Training loop
    steps_per_epoch = len(lr_train) // batch_size

    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs}")

        for step in range(steps_per_epoch):
            # Get batch
            idx = np.random.randint(0, len(lr_train), batch_size)
            lr_batch = lr_train[idx]
            hr_batch = hr_train[idx]
            y_batch = y_train[idx]

            # Train discriminator
            D.trainable = True
            sr_batch = G.predict(lr_batch, verbose=0)

            d_loss_real = D.train_on_batch(hr_batch, np.ones((batch_size, 1)))
            d_loss_fake = D.train_on_batch(sr_batch, np.zeros((batch_size, 1)))
            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)

            # Train generator through joint model
            D.trainable = False
            g_loss = joint_model.train_on_batch(
                [lr_batch, hr_batch],
                [np.ones((batch_size, 1)), y_batch]
            )

            if step % 10 == 0:
                print(f"Step {step}/{steps_per_epoch}")
                print(f"D loss: {d_loss[0]:.4f}, D acc: {d_loss[1]:.4f}")
                print(f"G loss: {g_loss[0]:.4f}, G acc: {g_loss[1]:.4f}")
                print(f"C acc: {g_loss[3]:.4f}")

        # Validation
        sr_test = G.predict(lr_test, verbose=0)
        sr_test_rgb = np.repeat(sr_test, 3, axis=-1)

        # Evaluate models
        d_val_loss = D.evaluate(sr_test, np.zeros((len(sr_test), 1)), verbose=0)
        c_val_loss = C.evaluate(sr_test_rgb, y_test, verbose=0)

        print("\nValidation Results:")
        print(f"D loss: {d_val_loss[0]:.4f}, D acc: {d_val_loss[1]:.4f}")
        print(f"C loss: {c_val_loss[0]:.4f}, C acc: {c_val_loss[1]:.4f}")

    return G, D, C

# Evaluation metrics
def evaluate_models(G, D, C, lr_test, hr_test, y_test):
    # Generate SR images
    sr_test = G.predict(lr_test)
    sr_test_rgb = np.repeat(sr_test, 3, axis=-1)

    # Get predictions
    y_pred = np.argmax(C.predict(sr_test_rgb), axis=1)
    y_true = np.argmax(y_test, axis=1)

    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    cm = confusion_matrix(y_true, y_pred)

    print("\nFinal Evaluation Metrics:")
    print(f"Accuracy : {accuracy*100:.2f}%")
    print(f"Precision: {precision*100:.2f}%")
    print(f"Recall   : {recall*100:.2f}%")
    print(f"F1 Score : {f1*100:.2f}%")
    print("\nConfusion Matrix:")
    print(cm)

    return accuracy, precision, recall, f1, cm

# Main execution
if __name__ == "__main__":
    # Train models
    G, D, C = train_models(original_images_dir)

    # Load test data
    X_lr, X_hr, y, class_names = prepare_dataset(original_images_dir)
    _, lr_test, _, hr_test, _, y_test = train_test_split(X_lr, X_hr, y, test_size=0.2)

    # Evaluate
    metrics = evaluate_models(G, D, C, lr_test, hr_test, y_test)

"""### Data Augmentation"""

def reset_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def augment_and_merge_images(images_dir, output_dir, target_count):
    # Refresh the entire output directory once
    reset_directory(output_dir)

    transform = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(p=0.2),
        A.Rotate(limit=15, p=0.5),
        A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.1, rotate_limit=15, p=0.5),
        A.GaussNoise(p=0.2),
    ])

    for class_name in os.listdir(images_dir):
        class_input_path = os.path.join(images_dir, class_name)
        if not os.path.isdir(class_input_path):
            continue

        output_class_path = os.path.join(output_dir, class_name)
        reset_directory(output_class_path)  # ✅ Refresh per class

        images = [img for img in os.listdir(class_input_path) if img.lower().endswith(('.jpg', '.jpeg', '.png'))]
        current_count = len(images)
        needed = target_count - current_count

        print(f"{class_name}: {current_count} images → augmenting {needed} to reach {target_count}")

        # Copy original images
        for img_name in images:
            src_path = os.path.join(class_input_path, img_name)
            dst_path = os.path.join(output_class_path, img_name)
            shutil.copy2(src_path, dst_path)

        # Generate augmented images
        i = 0
        while i < needed:
            img_name = images[i % len(images)]
            img_path = os.path.join(class_input_path, img_name)
            image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue

            image = cv2.resize(image, (96, 96)).astype(np.float32) / 255.0
            augmented = transform(image=image)['image']
            aug_img = (augmented * 255).astype(np.uint8)

            aug_name = f"{os.path.splitext(img_name)[0]}_aug{i+1}.png"
            aug_path = os.path.join(output_class_path, aug_name)
            cv2.imwrite(aug_path, aug_img)
            i += 1

        print(f"{class_name}: Finished with {len(os.listdir(output_class_path))} total images.")

# --- 1. Build Generator (used only for generating HR images)
lr_shape = (48, 48, 1)
generator = build_generator(input_shape=lr_shape)

# --- 2. Load original LR images and labels
original_images_dir = "/content/drive/MyDrive/Data_Visualization/Course_Project/images"
lr_imgs, _, image_names, class_labels = load_images(original_images_dir)

# --- 3. Generate and save SRGAN output images (96x96) to disk
srgan_output_dir = "/content/drive/MyDrive/Data_Visualization/Course_Project/srgan_images"
save_srgan_generated_images(generator, lr_imgs, image_names, class_labels, srgan_output_dir)

# --- 4. Augment the saved SRGAN outputs to balance dataset
target_count = 6834  # Highest class count or desired per-class target
augmented_output_dir = "/content/drive/MyDrive/Data_Visualization/Course_Project/srgan_augmented"
augment_and_merge_images(srgan_output_dir, augmented_output_dir, target_count)