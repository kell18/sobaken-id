from ultralytics import YOLO
import cv2
import os
import numpy as np
import json

# Load YOLO segmentation model (yolov8n-seg.pt)
model = YOLO('yolov8n-seg.pt')

# Define paths for images, saving segmented images, and annotations
image_folder = os.path.join('data', 'filtered_imgs')
save_folder = os.path.join('data', 'segmented_imgs')
annotation_file = os.path.join('data', 'annotations_coco.json')

# Create folder for saving images if it doesn't exist
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# List to store COCO-style annotations
annotations = {
    "images": [],
    "annotations": [],
    "categories": [
        {"id": 1, "name": "dog"},
        {"id": 2, "name": "cat"}
    ]
}

annotation_id = 1

# Iterate through all images in the folder
for image_id, image_name in enumerate(os.listdir(image_folder)):
    # Full path to the image
    image_path = os.path.join(image_folder, image_name)

    # Run the image through the model
    results = model(image_path)

    # Load the image using OpenCV
    img = cv2.imread(image_path)
    height, width, _ = img.shape

    # Add image info to the annotations
    annotations["images"].append({
        "id": image_id,
        "file_name": image_name,
        "height": height,
        "width": width
    })

    # Iterate through the predictions for each object in the image
    for result in results:
        if result.masks:  # Check if masks are predicted
            for mask, box in zip(result.masks.data, result.boxes):
                class_id = int(box.cls[0])  # Get the object class

                # Check class (16 - dog, 17 - cat)
                if class_id in [16, 17]:
                    # Assign category (1 - dog, 2 - cat)
                    category_id = 1 if class_id == 16 else 2

                    # Mask is already a binary image (array)
                    mask = mask.cpu().numpy()

                    # Resize the mask to fit the image dimensions
                    mask_resized = cv2.resize(mask, (width, height))

                    # Apply the mask to the image
                    img[mask_resized > 0.5] = [0, 255, 0]  # Green for segmented areas

                    # Get contours of the segmented area
                    contours, _ = cv2.findContours((mask_resized > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    segmentation = []

                    for contour in contours:
                        contour = contour.flatten().tolist()  # Convert to list
                        if len(contour) > 4:  # Segmentation must have at least 3 points
                            segmentation.append(contour)

                    # Create bounding box from the coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    bbox = [x1, y1, x2 - x1, y2 - y1]  # COCO format: [x_min, y_min, width, height]

                    # Convert values to standard float type
                    area = float(np.sum(mask_resized))  # Segmentation area

                    # Add annotation in COCO format
                    annotations["annotations"].append({
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": category_id,
                        "segmentation": segmentation,
                        "bbox": bbox,
                        "area": area,  # Use the converted area
                        "iscrowd": 0  # Not a "crowd" object
                    })
                    annotation_id += 1

    # Save segmented images with masks applied
    save_path = os.path.join(save_folder, image_name)
    cv2.imwrite(save_path, img)

# Save the annotations to a JSON file
with open(annotation_file, 'w') as f:
    json.dump(annotations, f)

print("Segmentation completed and annotations saved.")
