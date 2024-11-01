import os
import sys
import signal
import pickle
from collections import defaultdict
from PIL import Image
import imagehash
import shutil

#### Docs:
# Using Perceptual Hash model (pre-trained, used via imagehash lib):
# 1. Deduplicate imgs within each post
# 2. Deduplicate static images similar to what found in SPECIAL_ADS_DIRS
# 3. Remove all the posts with __at least 1 image in common__ except the one with the most images

# ----------------------- Configuration Parameters -----------------------

# Directories
BASE_IMAGES_DIRs = [
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_1',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_2',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_3',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_4',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_5',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_6',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_7',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_8',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_9',
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_10'
]
DUPLICATES_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/duplicates_parts'
SPECIAL_ADS_DIRS = [ '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/test/static_duplicates']
HASHES_FILE = 'image_hashes.pkl'  # File to save/load image hashes
PROGRESS_FILE = 'deduplication_progress.pkl'  # File to save/load progress

# Thresholds
INTRA_POST_THRESHOLD = 3  # Threshold for duplicates within a post
INTER_POST_THRESHOLD = 3  # Threshold for duplicates between posts

# ------------------------------------------------------------------------

# Global variables for progress saving
progress = {
    'image_location_map': {},  # Mapping for image locations
}

# Global variable for all image hashes
all_hashes = {}

# Handle graceful exit
def signal_handler(sig, frame):
    print('Interrupt received, saving progress...')
    save_progress()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def save_progress():
    with open(PROGRESS_FILE, 'wb') as f:
        pickle.dump(progress, f)
    print("Progress saved.")

def load_progress():
    global progress
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'rb') as f:
            progress = pickle.load(f)
        print("Progress loaded.")
    else:
        print("No previous progress found. Starting fresh.")

def compute_image_hashes():
    global all_hashes  # Declare as global to modify the global variable
    if os.path.exists(HASHES_FILE):
        with open(HASHES_FILE, 'rb') as f:
            all_hashes = pickle.load(f)
        print("Loaded image hashes from file.")
    else:
        all_hashes = {}
        print("Computing image hashes...")
        # Process base images
        image_paths = []
        for base_dir in BASE_IMAGES_DIRs:
            image_paths.extend(glob_images_in_directory(base_dir))
        for img_path in image_paths:
            img_hash = compute_phash(img_path)
            if img_hash is not None:
                all_hashes[img_path] = img_hash
                progress['image_location_map'][img_path] = img_path  # Initialize mapping

        # Process special ads images
        for special_dir in SPECIAL_ADS_DIRS:
            image_paths = glob_images_in_directory(special_dir)
            for img_path in image_paths:
                img_hash = compute_phash(img_path)
                if img_hash is not None:
                    all_hashes[img_path] = img_hash
                    progress['image_location_map'][img_path] = img_path  # Initialize mapping

        with open(HASHES_FILE, 'wb') as f:
            pickle.dump(all_hashes, f)
        print("Image hashes computed and saved.")
    return all_hashes

def glob_images_in_directory(directory):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    image_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(image_extensions):
                image_paths.append(os.path.join(root, file))
    return image_paths

def compute_phash(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img_hash = imagehash.phash(img)
        return img_hash
    except Exception as e:
        print(f"Error computing hash for {image_path}: {e}")
        return None

def get_post_id_from_path(image_path):
    # Assuming filenames are in the format: prefix_groupid_postid_imgnum.ext
    filename = os.path.basename(image_path)
    base_name, _ = os.path.splitext(filename)
    parts = base_name.split('_')
    if len(parts) >= 3:
        group_id = parts[-3]
        post_id = parts[-2]
        return f"{group_id}_{post_id}"
    else:
        return None

def deduplicate_within_posts():
    print("Deduplicating images within posts...")
    posts = defaultdict(list)
    for img_path, img_hash in all_hashes.items():
        post_id = get_post_id_from_path(img_path)
        if post_id:
            posts[post_id].append((img_path, img_hash))

    for post_id, img_list in posts.items():
        unique_hashes = {}
        for img_path, img_hash in img_list:
            duplicate_found = False
            for u_hash in unique_hashes.values():
                if abs(img_hash - u_hash) <= INTRA_POST_THRESHOLD:
                    duplicate_found = True
                    break
            if not duplicate_found:
                unique_hashes[img_path] = img_hash
            else:
                # Remove duplicate image
                current_path = progress['image_location_map'].get(img_path, img_path)
                if os.path.exists(current_path):
                    os.remove(current_path)
                    print(f"Removed duplicate image within post {post_id}: {current_path}")
                    del progress['image_location_map'][img_path]
                    del all_hashes[img_path]
                else:
                    print(f"File already removed: {current_path}")
    print("Intra-post deduplication complete.")

def remove_special_ads_images():
    print("Removing special ads images from base images...")
    special_hashes = set()
    for special_dir in SPECIAL_ADS_DIRS:
        for img_path in glob_images_in_directory(special_dir):
            img_hash = all_hashes.get(img_path)
            if img_hash:
                special_hashes.add(img_hash)

    for img_path in list(all_hashes.keys()):
        if any([img_path.startswith(b) for b in BASE_IMAGES_DIRs]):
            img_hash = all_hashes[img_path]
            for special_hash in special_hashes:
                if abs(img_hash - special_hash) <= INTRA_POST_THRESHOLD:
                    # Remove the image if it exists
                    current_path = progress['image_location_map'].get(img_path, img_path)
                    if os.path.exists(current_path):
                        os.remove(current_path)
                        print(f"Removed special ad image: {current_path}")
                        del progress['image_location_map'][img_path]
                        del all_hashes[img_path]
                    else:
                        print(f"File already removed: {current_path}")
                    break
    print("Special ads images removed.")

def deduplicate_across_posts():
    print("Deduplicating images across posts...")
    posts = defaultdict(set)
    for img_path, img_hash in all_hashes.items():
        post_id = get_post_id_from_path(img_path)
        if post_id:
            posts[post_id].add(img_hash)

    # Union-Find Data Structure
    parent = {}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]  # Path compression
            u = parent[u]
        return u

    def union(u, v):
        pu, pv = find(u), find(v)
        if pu != pv:
            parent[pv] = pu

    # Initialize parent pointers
    for post_id in posts:
        parent[post_id] = post_id

    # Build inverted index: hash -> set of post_ids
    hash_to_posts = defaultdict(set)
    for post_id, img_hashes in posts.items():
        for img_hash in img_hashes:
            hash_to_posts[img_hash].add(post_id)

    # Union posts that share similar images
    for img_hash, post_ids in hash_to_posts.items():
        post_ids = list(post_ids)
        for i in range(len(post_ids)):
            for j in range(i + 1, len(post_ids)):
                post_id1 = post_ids[i]
                post_id2 = post_ids[j]
                if find(post_id1) != find(post_id2):
                    union(post_id1, post_id2)

    # Group posts by their root parent
    clusters = defaultdict(set)
    for post_id in posts:
        root = find(post_id)
        clusters[root].add(post_id)

    # Handle duplicates within clusters
    duplicate_id_counter = 0
    for cluster_posts in clusters.values():
        if len(cluster_posts) > 1:
            # Collect images and counts
            post_images = {}
            for post_id in cluster_posts:
                img_hashes = posts[post_id]
                post_images[post_id] = img_hashes

            # Sort posts by number of images (for case 5.3)
            sorted_posts = sorted(post_images.items(), key=lambda x: len(x[1]), reverse=True)
            original_post_id = sorted_posts[0][0]

            # Handle according to the cases
            for post_id in cluster_posts:
                if post_id == original_post_id:
                    # Move images to originals dir (if required)
                    pass  # No action needed as per your updated requirements
                else:
                    # Move images to duplicates dir
                    duplicate_id_counter += 1
                    duplicate_id = f"dup{duplicate_id_counter:04d}"
                    move_post_images_to_duplicates(post_id, duplicate_id)

            print(f"Handled duplicate cluster: {cluster_posts} ({original_post_id} selected)")

    print("Inter-post deduplication complete.")

def move_post_images_to_duplicates(post_id, duplicate_id):
    for img_path in list(all_hashes.keys()):
        if get_post_id_from_path(img_path) == post_id:
            current_path = progress['image_location_map'].get(img_path, img_path)
            if os.path.exists(current_path):
                new_filename = f"{duplicate_id}_{os.path.basename(current_path)}"
                new_path = os.path.join(DUPLICATES_DIR, new_filename)
                shutil.move(current_path, new_path)
                progress['image_location_map'][img_path] = new_path  # Update mapping
                del all_hashes[img_path]  # Remove from hashes
            else:
                print(f"File already moved or missing: {current_path}")

def deduplication_loop():
    # Load progress if any
    load_progress()

    # Compute or load image hashes
    compute_image_hashes()

    global all_hashes
    # Update hashes to only include existing files
    all_hashes = {k: v for k, v in all_hashes.items() if os.path.exists(progress['image_location_map'].get(k, k))}

    # Step 3: Deduplicate within posts
    deduplicate_within_posts()

    # Step 4: Remove special ads images
    remove_special_ads_images()

    # Update hashes after removals
    all_hashes = {k: v for k, v in all_hashes.items() if os.path.exists(progress['image_location_map'].get(k, k))}

    # Step 5: Deduplicate across posts
    deduplicate_across_posts()

    print("Deduplication process completed.")

def main():
    deduplication_loop()

if __name__ == "__main__":
    main()
