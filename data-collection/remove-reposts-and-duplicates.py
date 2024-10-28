import os
import glob
from PIL import Image
import imagehash
from tqdm import tqdm
import shutil
import gc

# TODO - use higher threshold for images in different posts

"""
input_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/imgs_dedup'
output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/imgs_dedup_dedup'
duplicates_output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/duplicates_among_dedup'
"""

input_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/raw_dedupX2_clean_dom_lapkin_1-3'
output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/raw_dedupX3_clean_dom_lapkin_1-3'
duplicates_output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/x2DUPLICATES_raw_dom_lapkin_1-3'

def remove_duplicate_images(input_dir, unique_output_dir, duplicates_output_dir, hash_size=8, threshold=5, batch_size=10000):
    """
    Removes duplicate images from the input directory based on perceptual hashing.
    Images are considered duplicates if the Hamming distance between their hashes is less than or equal to the threshold.
    Saves unique images to the unique_output_dir and copies duplicate images with prefixed filenames to the duplicates_output_dir for inspection.

    Parameters:
    - input_dir: Path to the directory containing images.
    - unique_output_dir: Path to the directory to save unique images.
    - duplicates_output_dir: Path to the directory to save duplicate images.
    - hash_size: Size of the hash; higher values are more precise but slower.
    - threshold: Maximum Hamming distance between hashes to consider images as duplicates.
    - batch_size: Number of images to process in each batch.
    """
    # Create the output directories if they don't exist
    if os.path.exists(unique_output_dir) and os.path.isdir(unique_output_dir):
        shutil.rmtree(unique_output_dir)
    if os.path.exists(duplicates_output_dir) and os.path.isdir(duplicates_output_dir):
        shutil.rmtree(duplicates_output_dir)
    os.makedirs(unique_output_dir, exist_ok=True)
    os.makedirs(duplicates_output_dir, exist_ok=True)

    # Collect all image paths
    image_paths = glob.glob(os.path.join(input_dir, '*.*'))  # Adjust the pattern if needed
    total_images = len(image_paths)

    # List to store image infos
    image_infos = []

    print("Processing images and computing hashes...")
    for batch_start in range(0, total_images, batch_size):
        batch_paths = image_paths[batch_start:batch_start+batch_size]
        for img_path in tqdm(batch_paths, desc=f"Batch {batch_start//batch_size + 1}"):
            try:
                with Image.open(img_path) as img:
                    img = img.convert('RGB')
                    # Compute perceptual hash
                    img_hash = imagehash.phash(img, hash_size=hash_size)
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue

            # Store image info
            filename = os.path.basename(img_path)
            image_info = {
                'img_path': img_path,
                'filename': filename,
                'hash': img_hash,
                'duplicate_id': None,  # Will be assigned if the image is a duplicate
            }
            image_infos.append(image_info)

        # Optional: clear memory if needed
        gc.collect()

    print("Analyzing duplicates based on Hamming distance...")
    # Dictionary to keep track of which images have been processed
    processed_indices = set()
    duplicate_id_counter = 0

    # Loop through all images and compare hashes
    for i in tqdm(range(len(image_infos)), desc="Comparing images"):
        if i in processed_indices:
            continue
        img_info_1 = image_infos[i]
        duplicates = []
        for j in range(i+1, len(image_infos)):
            if j in processed_indices:
                continue
            img_info_2 = image_infos[j]
            # Compute Hamming distance between hashes
            distance = img_info_1['hash'] - img_info_2['hash']
            if distance <= threshold:
                duplicates.append(img_info_2)
                processed_indices.add(j)
        if duplicates:
            # Assign duplicate_id
            duplicate_id_counter += 1
            duplicate_id = f"dup{duplicate_id_counter:04d}"
            img_info_1['duplicate_id'] = duplicate_id
            # Copy the first image (original) to unique_output_dir
            original_output_path = os.path.join(unique_output_dir, img_info_1['filename'])
            if not os.path.exists(original_output_path):
                shutil.copy2(img_info_1['img_path'], original_output_path)
            # Copy duplicates to duplicates_output_dir
            for dup_info in duplicates:
                dup_info['duplicate_id'] = duplicate_id
                new_dupl_filename = f"{duplicate_id}_{dup_info['filename']}"
                new_orig_dupl_filename = f"{duplicate_id}_{img_info_1['filename']}"
                duplicate_output_path = os.path.join(duplicates_output_dir, new_dupl_filename)
                orig_dupl_output_path = os.path.join(duplicates_output_dir, new_orig_dupl_filename)
                if not os.path.exists(duplicate_output_path):
                    shutil.copy2(dup_info['img_path'], duplicate_output_path)
                if not os.path.exists(orig_dupl_output_path):
                    shutil.copy2(img_info_1['img_path'], orig_dupl_output_path)
        else:
            # No duplicates found, copy image to unique_output_dir
            original_output_path = os.path.join(unique_output_dir, img_info_1['filename'])
            if not os.path.exists(original_output_path):
                shutil.copy2(img_info_1['img_path'], original_output_path)
        processed_indices.add(i)

    print("Duplicate removal complete.")
    print(f"Unique images saved to: {unique_output_dir}")
    print(f"Duplicate images saved to: {duplicates_output_dir}")

if __name__ == '__main__':
    remove_duplicate_images(
        input_dir=input_directory,
        unique_output_dir=output_directory,
        duplicates_output_dir=duplicates_output_directory,
        hash_size=8,
        threshold=8,
        batch_size=10000
    )
