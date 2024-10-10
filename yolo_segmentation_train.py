from ultralytics import YOLO
from sklearn.model_selection import train_test_split
import os

# Path to the folder with images and labels
image_folder = os.path.join('dog_dataset', 'images')
label_folder = os.path.join('dog_dataset', 'labels')

images = [os.path.join(image_folder, f) for f in os.listdir(image_folder)]
labels = [os.path.join(label_folder, f) for f in os.listdir(label_folder)]

# Separation of data into training and validation samples
train_images, val_images, train_labels, val_labels = train_test_split(images, labels, test_size=0.2, random_state=42)

# Saving image paths to the files train_images.txt and val_images.txt
with open(os.path.join('dog_dataset', 'train_images.txt'), 'w') as f:
    for img in train_images:
        f.write(f"{img}\n")

with open(os.path.join('dog_dataset', 'val_images.txt'), 'w') as f:
    for img in val_images:
        f.write(f"{img}\n")

# Path to the data.yaml file
data_yaml = os.path.join('dog_dataset', 'data.yaml')

# Загрузка предобученной модели YOLOv8
model = YOLO('yolov8n-seg.pt')

# Training of the model divided into training and validation samples
model.train(
    data=data_yaml,         # path to the data.yaml
    epochs=200,              # num of epochs
    imgsz=640,              # image size
    batch=16,               # batch size
    lr0=0.01,               # initial learning rate
    weight_decay=0.0005,    # weight regularisation
    lrf=0.2,                # finite learning rate
    freeze=10,              # freezing of the first N layers
    accumulate=2,           # gradient accumulation
    device='0,1'            # using multiple GPUs, if available
)

# Saving the trained model
model.save("dog_detection_model.pt")

# Evaluating the model using validation metrics
metrics = model.val()

# Print metrics
print("Model Performance:")
print(f"Precision: {metrics['metrics/precision(B)']}")
print(f"Recall: {metrics['metrics/recall(B)']}")
print(f"mAP@0.50: {metrics['metrics/mAP50(B)']}")
print(f"mAP@0.50:0.95: {metrics['metrics/mAP50-95(B)']}")