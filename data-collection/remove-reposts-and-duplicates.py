import os
import glob
from PIL import Image
import imagehash
from tqdm import tqdm
import shutil
import gc

def remove_duplicate_images(input_dir, unique_output_dir, duplicates_output_dir, hash_size=8, threshold=5, batch_size=10000):
    """
    Optimized version for large datasets.
    """
    # Create the output directories if they don't exist
    os.makedirs(unique_output_dir, exist_ok=True)
    os.makedirs(duplicates_output_dir, exist_ok=True)

    # Collect all image paths
    image_paths = glob.glob(os.path.join(input_dir, '*.*'))  # Adjust the pattern if needed
    total_images = len(image_paths)

    # Dictionaries to store hashes and image info
    hashes = {}  # Key: hash, Value: list of image infos
    post_images = {}  # Key: (group_id, post_id), Value: list of image infos

    print("Processing images and computing hashes...")
    for batch_start in range(0, total_images, batch_size):
        batch_paths = image_paths[batch_start:batch_start+batch_size]
        batch_image_infos = []  # List to hold image infos for the current batch

        for img_path in tqdm(batch_paths, desc=f"Batch {batch_start//batch_size + 1}"):
            try:
                with Image.open(img_path) as img:
                    img = img.convert('RGB')
                    # Compute perceptual hash
                    img_hash = imagehash.phash(img, hash_size=hash_size)
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue

            # Extract group_id, post_id, img_num from the filename
            filename = os.path.basename(img_path)
            base_name, ext = os.path.splitext(filename)
            parts = base_name.split('_')
            if len(parts) == 3:
                group_id, post_id, img_num = parts
            else:
                print(f"Filename {filename} does not match expected format. Skipping.")
                continue

            # Store image info
            image_info = {
                'img_path': img_path,
                'filename': filename,
                'group_id': group_id,
                'post_id': post_id,
                'img_num': img_num,
                'ext': ext,
                'hash': img_hash,
                'is_duplicate': False,  # Will be updated later
                'duplicate_with': None,  # (group_id, post_id) of the selected image
                'duplicate_id': None,    # Unique ID for duplicate group
            }
            batch_image_infos.append(image_info)

            # Add image to post_images
            post_key = (group_id, post_id)
            post_images.setdefault(post_key, []).append(image_info)

            # Add image to hashes dict
            hashes.setdefault(img_hash, []).append(image_info)

        # No need to keep batch_image_infos beyond this point
        del batch_image_infos
        gc.collect()  # Explicitly invoke garbage collection

    print("Analyzing duplicates across posts and groups...")
    # Assign a unique duplicate ID per group of duplicates
    duplicate_id_counter = 0
    for img_hash, imgs in hashes.items():
        # Initialize duplicate_id for this hash if duplicates are found
        if len(imgs) > 1:
            duplicate_id_counter += 1
            duplicate_id = f"dup{duplicate_id_counter:04d}"
            # Identify duplicates across posts/groups
            posts_with_hash = {}
            for img_info in imgs:
                post_key = (img_info['group_id'], img_info['post_id'])
                posts_with_hash.setdefault(post_key, []).append(img_info)
            # If duplicates are in multiple posts
            if len(posts_with_hash) > 1:
                # Sort post_keys to determine which post to keep
                sorted_post_keys = sorted(posts_with_hash.keys())
                selected_post_key = sorted_post_keys[0]  # Keep the first post
                for post_key in sorted_post_keys[1:]:
                    for img_info in posts_with_hash[post_key]:
                        img_info['is_duplicate'] = True
                        img_info['duplicate_with'] = selected_post_key
                        img_info['duplicate_id'] = duplicate_id
            else:
                # Duplicates within the same post, no action needed
                continue

    print("Identifying posts with all images as duplicates...")
    # Determine which posts have all images as duplicates
    posts_to_remove = {}
    for post_key, imgs in post_images.items():
        all_duplicates = all(img_info.get('is_duplicate', False) for img_info in imgs)
        if all_duplicates:
            # Get the selected_post_key that these images are duplicates of
            duplicate_with_keys = set(img_info['duplicate_with'] for img_info in imgs)
            if len(duplicate_with_keys) == 1:
                duplicate_with_key = duplicate_with_keys.pop()
                posts_to_remove[post_key] = duplicate_with_key
                # print(f"All images in post {post_key} are duplicates with post {duplicate_with_key}. Marking for removal.")
            else:
                print(f"Post {post_key} has images duplicated with multiple posts. Skipping.")

    # Now, process images again to copy them to the appropriate directories
    print("Copying images to output directories...")
    for img_hash, imgs in tqdm(hashes.items(), desc="Copying images"):
        for img_info in imgs:
            post_key = (img_info['group_id'], img_info['post_id'])
            img_path = img_info['img_path']
            filename = img_info['filename']
            ext = img_info['ext']
            if post_key in posts_to_remove:
                # Skip images from posts marked for removal
                continue
            if img_info.get('is_duplicate', False):
                # Duplicate image, but not from a post to be removed
                # Copy to duplicates_output_dir with new naming convention
                duplicate_with_key = img_info['duplicate_with']
                duplicate_id = img_info['duplicate_id']
                # For partial duplicates
                new_filename = f"{duplicate_id}_{img_info['group_id']}-{img_info['post_id']}-{img_info['img_num']}{ext}"
                output_path = os.path.join(duplicates_output_dir, new_filename)
                if not os.path.exists(output_path):
                    shutil.copy2(img_path, output_path)
            else:
                # Unique image, copy to unique_output_dir
                output_path = os.path.join(unique_output_dir, filename)
                if not os.path.exists(output_path):
                    shutil.copy2(img_path, output_path)

    # Copy images from posts marked for removal to duplicates_output_dir for inspection
    print("Copying images from posts marked for removal to duplicates output directory...")
    for removed_post_key, selected_post_key in posts_to_remove.items():
        # Create subdirectory per duplicate_id
        duplicate_id = None
        # Find the duplicate_id for this group of duplicates
        for img_info in post_images[removed_post_key]:
            if img_info.get('duplicate_id'):
                duplicate_id = img_info['duplicate_id']
                break
        if duplicate_id is None:
            # Assign a new duplicate_id if not found (should not happen)
            duplicate_id_counter += 1
            duplicate_id = f"dup{duplicate_id_counter:04d}"

        # Copy images from the removed post
        for img_info in post_images[removed_post_key]:
            img_path = img_info['img_path']
            ext = img_info['ext']
            new_filename = f"p{duplicate_id}_{img_info['group_id']}-{img_info['post_id']}-{img_info['img_num']}{ext}"
            output_path = os.path.join(duplicates_output_dir, new_filename)
            if not os.path.exists(output_path):
                shutil.copy2(img_path, output_path)

        # Also copy images from the selected post
        for img_info in post_images[selected_post_key]:
            img_path = img_info['img_path']
            ext = img_info['ext']
            new_filename = f"{duplicate_id}_{img_info['group_id']}-{img_info['post_id']}-{img_info['img_num']}{ext}"
            output_path = os.path.join(duplicates_output_dir, new_filename)
            if not os.path.exists(output_path):
                shutil.copy2(img_path, output_path)

    print("Duplicate removal complete.")
    print(f"Unique images saved to: {unique_output_dir}")
    print(f"Duplicate images saved to: {duplicates_output_dir}")

if __name__ == '__main__':
    input_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/imgs'
    output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/imgs_dedup'
    duplicates_output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/duplicates'

    remove_duplicate_images(
        input_dir=input_directory,
        unique_output_dir=output_directory,
        duplicates_output_dir=duplicates_output_directory,
        hash_size=8,
        threshold=5,
        batch_size=10000  # Adjust batch size as needed
    )
