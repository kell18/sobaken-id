import json
import numpy as np
import os
import cv2
from ultralytics import YOLO
from pycocotools import mask as mask_util

# Load YOLO segmentation model (yolov8n-seg.pt)
model = YOLO('yolov8n-seg.pt')

# Define paths for images, saving segmented images, and annotations
image_folder = os.path.join('data', 'filtered_imgs')
save_folder = os.path.join('data', 'segmented_imgs')
annotation_file = os.path.join('data', 'annotations_coco.json')

# Ensure the save folder exists
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# Initialize annotations dictionary in COCO format
annotations = {
    "images": [],
    "annotations": [],
    "categories": [
        {"id": 1, "name": "dog"},
        {"id": 2, "name": "cat"}
    ]
}

annotation_id = 1

# Function to convert numpy array or bytes to serializable format
def convert_to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert numpy array to a Python list
    if isinstance(obj, bytes):
        return obj.decode()  # Decode bytes to string
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Process each image in the folder
for image_id, image_name in enumerate(os.listdir(image_folder)):
    # Full path to the image
    image_path = os.path.join(image_folder, image_name)

    # Run the image through the model
    results = model(image_path)

    # Load the image with OpenCV
    img = cv2.imread(image_path)
    height, width, _ = img.shape

    # Add image info to the COCO-style annotations
    annotations["images"].append({
        "id": image_id,
        "file_name": image_name,
        "height": height,
        "width": width
    })

    # Loop through each detected object
    for result in results:
        if result.masks:  # Check if masks exist in the predictions
            for mask, box in zip(result.masks.data, result.boxes):
                class_id = int(box.cls[0])  # Get the class ID

                # Check if it's a dog or cat (16 for dog, 17 for cat)
                if class_id in [16, 17]:
                    # Set the category ID (1 for dog, 2 for cat)
                    category_id = 1 if class_id == 16 else 2

                    # Convert mask to numpy array
                    mask = mask.cpu().numpy()

                    # Resize mask to the image size
                    mask_resized = cv2.resize(mask, (width, height))

                    # Apply the mask to the image (visualization purposes)
                    img[mask_resized > 0.5] = [0, 255, 0]  # Green color for segmented areas

                    # Use pycocotools to encode the mask into RLE format
                    rle = mask_util.encode(np.asfortranarray((mask_resized > 0.5).astype(np.uint8)))

                    # Get bounding box coordinates and convert to COCO format
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    bbox = [x1, y1, x2 - x1, y2 - y1]  # COCO format: [x_min, y_min, width, height]

                    # Convert mask area to a serializable float value
                    area = float(np.sum(mask_resized))

                    # Add the annotation in COCO format
                    annotations["annotations"].append({
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": category_id,
                        "segmentation": rle,  # Store the RLE-encoded mask
                        "bbox": bbox,
                        "area": area,
                        "iscrowd": 0  # Set 'iscrowd' to 0 for individual objects
                    })
                    annotation_id += 1

    # Save the image with the applied mask
    save_path = os.path.join(save_folder, image_name)
    cv2.imwrite(save_path, img)

# Save the COCO annotations to a JSON file
with open(annotation_file, 'w') as f:
    json.dump(annotations, f, default=convert_to_serializable)

print("Segmentation completed and annotations saved in COCO format")
