import os
import glob
from PIL import Image
import imagehash
from tqdm import tqdm
import shutil

def remove_duplicate_images(input_dir, unique_output_dir, duplicates_output_dir, hash_size=8, threshold=5):
    """
    Removes duplicate images from the input directory, considering images as duplicates
    only if they come from different posts (post-id in filename). If all images from a post
    are duplicates with images from newer posts, remove all images from the older post.
    Saves unique images to the unique_output_dir and copies duplicate images with prefixed
    filenames to the duplicates_output_dir for inspection.

    Parameters:
    - input_dir: Path to the directory containing images.
    - unique_output_dir: Path to the directory to save unique images.
    - duplicates_output_dir: Path to the directory to save duplicate images.
    - hash_size: Size of the hash; higher values are more precise but slower.
    - threshold: Maximum difference between hashes to consider images as duplicates.
    """
    # Create the output directories if they don't exist
    os.makedirs(unique_output_dir, exist_ok=True)
    os.makedirs(duplicates_output_dir, exist_ok=True)

    # Collect all image paths
    image_paths = glob.glob(os.path.join(input_dir, '*.*'))  # Adjust the pattern if needed

    # Dictionaries to store hashes and image info
    hashes = {}  # Key: hash, Value: list of image infos
    image_infos = []  # List of all image infos
    post_images = {}  # Key: post_id, Value: list of image infos
    duplicate_images = set()  # Set of image paths that are duplicates to be removed

    print("Processing images and computing hashes...")
    for img_path in tqdm(image_paths, desc="Computing image hashes"):
        try:
            img = Image.open(img_path).convert('RGB')
            # Compute perceptual hash
            img_hash = imagehash.phash(img, hash_size=hash_size)
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            continue

        # Extract post-id from the filename
        filename = os.path.basename(img_path)
        base_name, _ = os.path.splitext(filename)
        if '_' in base_name:
            post_id, _ = base_name.split('_', 1)
        else:
            print(f"Filename {filename} does not match expected format. Skipping.")
            continue

        # Store image info
        image_info = {
            'img_path': img_path,
            'post_id': post_id,
            'hash': img_hash,
            'is_duplicate': False,  # Will be updated later
            'duplicate_with': None,  # Post ID of the newer post
        }
        image_infos.append(image_info)

        # Add image to post_images
        if post_id not in post_images:
            post_images[post_id] = []
        post_images[post_id].append(image_info)

        # Add image to hashes dict
        if img_hash not in hashes:
            hashes[img_hash] = []
        hashes[img_hash].append(image_info)

    print("Analyzing duplicates across posts...")
    # Analyze duplicates
    for img_hash, imgs in hashes.items():
        # Check for duplicates across different posts
        posts_with_hash = {}
        for img_info in imgs:
            post_id = img_info['post_id']
            posts_with_hash.setdefault(post_id, []).append(img_info)
        if len(posts_with_hash) > 1:
            # Sort post_ids to determine older and newer posts
            sorted_post_ids = sorted(posts_with_hash.keys(), key=lambda x: int(x))
            for i in range(len(sorted_post_ids)-1):
                older_post_id = sorted_post_ids[i]
                newer_post_ids = sorted_post_ids[i+1:]
                for newer_post_id in newer_post_ids:
                    # Mark images from older post as duplicates if they have matching images in newer posts
                    for img_info in posts_with_hash[older_post_id]:
                        for new_img_info in posts_with_hash[newer_post_id]:
                            # Compute Hamming distance between hashes (should be zero since hashes are equal)
                            difference = img_info['hash'] - new_img_info['hash']
                            if difference <= threshold:
                                img_info['is_duplicate'] = True
                                img_info['duplicate_with'] = newer_post_id
                                duplicate_images.add(img_info['img_path'])
                                break  # Only need to find one duplicate
                        if img_info['is_duplicate']:
                            break  # Move to next image

    print("Identifying posts with all images as duplicates...")
    # Determine which posts have all images as duplicates
    posts_to_remove = {}
    for post_id, imgs in post_images.items():
        all_duplicates = all(img_info['is_duplicate'] for img_info in imgs)
        if all_duplicates:
            # Check if duplicates are with newer posts
            duplicate_with_newer_post = any(
                int(img_info['duplicate_with']) > int(post_id) for img_info in imgs if img_info['duplicate_with']
            )
            if duplicate_with_newer_post:
                newer_post_id = imgs[0]['duplicate_with']
                posts_to_remove[post_id] = newer_post_id
                print(f"All images in post {post_id} are duplicates with newer posts. Marking for removal.")

    # Copy unique images to the unique_output_dir
    print("Copying unique images to the unique output directory...")
    for img_info in image_infos:
        post_id = img_info['post_id']
        img_path = img_info['img_path']
        filename = os.path.basename(img_path)
        if post_id in posts_to_remove:
            # Skip images from posts marked for removal
            continue
        if img_info['is_duplicate']:
            # Duplicate image, but not from a post to be removed
            # Copy to duplicates_output_dir with prefixed filename
            duplicate_with_post_id = img_info['duplicate_with']
            new_filename = f"dupl{duplicate_with_post_id}_{filename}"
            output_path = os.path.join(duplicates_output_dir, new_filename)
            shutil.copy2(img_path, output_path)
        else:
            # Unique image, copy to unique_output_dir
            output_path = os.path.join(unique_output_dir, filename)
            shutil.copy2(img_path, output_path)

    # Optionally, copy images from posts to be removed to duplicates_output_dir for inspection
    print("Copying images from posts marked for removal to duplicates output directory...")
    for dupl_post_id, new_post_id in posts_to_remove.items():
        imgs = post_images[dupl_post_id]
        for img_info in imgs:
            img_path = img_info['img_path']
            filename = os.path.basename(img_path)
            new_filename = f"rm_post{dupl_post_id}_to{new_post_id}_{filename}"
            output_path = os.path.join(duplicates_output_dir, new_filename)
            shutil.copy2(img_path, output_path)

    print("Duplicate removal complete.")
    print(f"Unique images saved to: {unique_output_dir}")
    print(f"Duplicate images saved to: {duplicates_output_dir}")

if __name__ == '__main__':
    input_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/raw_clean_dom_lapkin_1-3'
    output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/raw_dedup_clean_dom_lapkin_1-3'
    duplicates_output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/DUPLICATES_raw_dom_lapkin_1-3'

    remove_duplicate_images(
        input_dir=input_directory,
        unique_output_dir=output_directory,
        duplicates_output_dir=duplicates_output_directory,
        hash_size=8,
        threshold=5
    )