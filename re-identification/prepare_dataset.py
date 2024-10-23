import os
import glob
import shutil
import random
from tqdm import tqdm
from PIL import Image

def process_dataset(input_dir, output_dir, target_size=(128, 256)):
    # Collect all image paths
    image_paths = glob.glob(os.path.join(input_dir, '*.jpg'))

    # Build a mapping from post-id to list of images
    post_id_to_images = {}
    for image_path in image_paths:
        filename = os.path.basename(image_path)
        base_name, ext = os.path.splitext(filename)
        if '_' in base_name:
            post_id, image_num = base_name.split('_', 1)
        else:
            print(f"Skipping file with unexpected format: {filename}")
            continue

        if post_id not in post_id_to_images:
            post_id_to_images[post_id] = []
        post_id_to_images[post_id].append(image_path)

    # Filter out post-ids with only one image
    filtered_post_ids = {pid: imgs for pid, imgs in post_id_to_images.items() if len(imgs) > 1}

    print(f"Total identities with more than one image: {len(filtered_post_ids)}")

    # Split post-ids into train and test sets
    post_ids = list(filtered_post_ids.keys())
    random.shuffle(post_ids)
    num_train = int(len(post_ids) * 0.7)  # 70% for training
    train_ids = post_ids[:num_train]
    test_ids = post_ids[num_train:]

    print(f"Training identities: {len(train_ids)}, Testing identities: {len(test_ids)}")

    # Prepare output directories
    train_dir = os.path.join(output_dir, 'train')
    query_dir = os.path.join(output_dir, 'query')
    gallery_dir = os.path.join(output_dir, 'gallery')

    # Remove existing directories if they exist to avoid mixing old data
    if os.path.exists(train_dir):
        shutil.rmtree(train_dir)
    if os.path.exists(query_dir):
        shutil.rmtree(query_dir)
    if os.path.exists(gallery_dir):
        shutil.rmtree(gallery_dir)

    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(query_dir, exist_ok=True)
    os.makedirs(gallery_dir, exist_ok=True)

    # Process training identities
    for pid in tqdm(train_ids, desc='Processing training identities'):
        img_paths = filtered_post_ids[pid]
        pid_dir = os.path.join(train_dir, pid)
        os.makedirs(pid_dir, exist_ok=True)
        for img_path in img_paths:
            img = process_image(img_path, target_size)
            filename = clean_file_name(img_path)
            img.save(os.path.join(pid_dir, filename))

    # Process testing identities
    for pid in tqdm(test_ids, desc='Processing testing identities'):
        img_paths = filtered_post_ids[pid]
        if len(img_paths) < 2:
            print(f"Not enough images for identity {pid} to split into query and gallery.")
            continue
        random.shuffle(img_paths)
        query_img_path = img_paths[0]
        gallery_img_paths = img_paths[1:]

        # Ensure gallery_img_paths is not empty TODO rm
        if not gallery_img_paths:
            print(f"No gallery images for identity {pid}. Moving image from query to gallery.")
            gallery_img_paths.append(query_img_path)
            query_img_path = gallery_img_paths.pop(0)
            # If still empty, skip the identity
            if not gallery_img_paths:
                print(f"Still no gallery images for identity {pid}. Skipping identity.")
                continue

        # Process query image
        img = process_image(query_img_path, target_size)
        img.save(os.path.join(query_dir, clean_file_name(query_img_path)))

        # Process gallery images
        for img_path in gallery_img_paths:
            img = process_image(img_path, target_size)
            img.save(os.path.join(gallery_dir, clean_file_name(img_path)))

    print("Dataset processing complete.")

def clean_file_name(img_path):
    filename = os.path.basename(img_path)
    return str(filename.replace('_segmented', ''))

def process_image(image_path, target_size):
    # Load image
    img = Image.open(image_path).convert('RGB')

    # Resize and pad image to target size
    img = pad_and_resize(img, target_size)

    return img

def pad_and_resize(img, target_size):
    # Resize image while maintaining aspect ratio
    img.thumbnail(target_size, Image.ANTIALIAS)
    # Create a new image with the target size and paste the resized image onto it
    new_img = Image.new('RGB', target_size, (0, 0, 0))
    left = (target_size[0] - img.width) // 2
    top = (target_size[1] - img.height) // 2
    new_img.paste(img, (left, top))
    return new_img

if __name__ == '__main__':
    input_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/segmented/segm_no-art_dom_lapkin_1-3__FLAT_AREA'
    output_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/clean/clean_dom_lapkin_1-3'

    # Set random seed for reproducibility
    random.seed(42)

    process_dataset(input_directory, output_directory, target_size=(128, 256))
