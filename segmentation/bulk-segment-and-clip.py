import os
import glob
import cv2
import numpy as np
from tqdm import tqdm
from pixellib.torchbackend.instance import instanceSegmentation


def segment_images(input_raw_ds_path, output_segmented_ds_dir, model_path,
                   save_as_flat_files=False, best_mask_based_on_area=False):
    # Initialize the segmentation model
    segmenter = instanceSegmentation()
    segmenter.load_model(model_path)

    # Define the target animal classes (you can adjust this list as needed)
    target_classes = segmenter.select_target_classes(cat=True, dog=True, bear=True, bird=True, horse=True,
                                                     sheep=True, cow=True)

    # Collect all images in the input directory
    image_paths = glob.glob(os.path.join(input_raw_ds_path, '*.jpg'))

    # Process images individually (tqdm thingy prints the processing status in the console)
    for image_path in tqdm(image_paths, desc="Segmenting images"):
        filename = os.path.basename(image_path)
        base_name, ext = os.path.splitext(filename)
        if '_' in base_name:
            post_id, image_num = base_name.split('_')
        else:
            print(f"Skipping file with unexpected format: {filename}")
            continue

        # Read the image
        image = cv2.imread(image_path)

        # Segment the image
        result = segmenter.segmentImage(
            image_path,
            extract_segmented_objects=True,
            save_extracted_objects=False,  # We'll handle saving manually
            segment_target_classes=target_classes,
            show_bboxes=False,
            output_image_name=None  # We don't need the output image with masks
        )

        # Get details of detected objects
        object_info = result[0]

        if best_mask_based_on_area:
            best_mask_index = find_best_area_mask_ind(object_info)
        else:
            best_mask_index = find_top_score_mask_ind(object_info)
        if best_mask_index is None:
            print(f"No target objects found in image: {filename}")
            continue

        # Get the mask of the object with the highest score
        best_mask = object_info['masks'][:, :, best_mask_index]

        # Extract the object using the mask
        masked_image = apply_mask_and_crop(image, best_mask)

        # Save the segmented object image
        if save_as_flat_files:
            final_output_dir = output_segmented_ds_dir
        else:
            final_output_dir = os.path.join(output_segmented_ds_dir, post_id)
            # Create the final output directory for this animal (post_id)
            os.makedirs(final_output_dir, exist_ok=True)

        # Save the image with a meaningful name
        output_image_path = os.path.join(final_output_dir, f"{post_id}_{image_num}.jpg")
        cv2.imwrite(output_image_path, masked_image)

    print("Segmentation and organization complete.")


def find_top_score_mask_ind(object_info: dict):
    max_score = 0
    max_index = None
    for idx, score in enumerate(object_info['scores']):
        if score > max_score:
            max_score = score
            max_index = idx
    return max_index


def find_best_area_mask_ind(object_info: dict):
    # Check if any target objects are detected
    num_objects = len(object_info['scores'])
    if num_objects == 0:
        return None

    elif num_objects == 1:
        # Only one object detected, use it as it is
        return 0

    else:
        # More than one object detected
        # Get the indices of objects sorted by confidence scores (descending)
        sorted_indices = np.argsort(object_info['scores'])[::-1]
        # Take the top three objects
        top_three_indices = sorted_indices[:3]

        # Compute the area (number of pixels) for each of the top three masks
        areas = []
        for idx in top_three_indices:
            mask = object_info['masks'][:, :, idx]
            area = np.sum(mask)
            areas.append(area)

        # Select the index with the largest area among the top three
        max_area_index = np.argmax(areas)
        return top_three_indices[max_area_index]


def apply_mask_and_crop(image, mask):
    # Apply the mask to the image to extract the object
    mask = mask.astype(bool)
    # Extract the object
    result = image * mask[:, :, None]

    # Find the bounding box of the non-zero regions in the mask
    coords = cv2.findNonZero(mask.astype(np.uint8))
    x, y, w, h = cv2.boundingRect(coords)

    # Crop the result to the bounding box
    cropped_result = result[y:y + h, x:x + w]

    return cropped_result


if __name__ == '__main__':
    input_directories = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/raw_dedup_clean_dom_lapkin_1-3'
    output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/segmented/segm_dom_lapkin_1-3__FLAT_AREA'
    model_file = '/Users/albert.bikeev/Projects/sobaken-id/trained_models/segm_PixelLib_pointrend_resnet50.pkl'

    segment_images(input_directories, output_directory, model_file,
                   save_as_flat_files=True, best_mask_based_on_area=True)
