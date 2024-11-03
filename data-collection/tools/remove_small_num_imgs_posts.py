import os
from collections import defaultdict
from file_name_info import FileNameInfo

# ----------------------------- Configuration -----------------------------

# Path to the directory containing the images
ROOT_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/segmented/vk_posts/part_3_only2_or_more_photos'  # Update this path accordingly

# Minimum number of images required for a post to be retained
MIN_IMAGES_THRESHOLD = 2  # Default is 1; change as needed

SUPPORTED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png']

# ---------------------------------------------------------------------------


def remove_small_num_imgs_posts(root_dir, min_images=1):
    """
    Removes images belonging to posts that have only 'min_images' images.

    Args:
        root_dir (str): Directory containing the images.
        min_images (int): Posts with this num of images or lower will be removed.

    Returns:
        int: Number of images removed.
    """
    removed_count = 0
    groups = defaultdict(list)
    all_files =  [f for f in os.listdir(root_dir) if any([ex for ex in SUPPORTED_IMAGE_EXTENSIONS if f.endswith(ex)])]

    # Group files by (GROUP_ID, POST_ID)
    for filename in all_files:
        filepath = os.path.join(root_dir, filename)
        if os.path.isfile(filepath):
            file_info = FileNameInfo.from_full_path(filepath)
            group_id, post_id = file_info.group_id, file_info.post_id
            if group_id and post_id:
                groups[(group_id, post_id)].append(filename)
            else:
                print(f"Skipping file with unexpected format: {filename}")

    print(f"\nTotal unique posts found: {len(groups)}")

    # Remove images from posts that have <= min_images
    print("\nRemoving posts with single or fewer images...")
    for (group_id, post_id), files in groups.items():
        if len(files) <= min_images:
            for file in files:
                file_to_remove = os.path.join(root_dir, file)
                try:
                    os.remove(file_to_remove)
                    removed_count += 1
                    print(f"Removed image: {file}")
                except Exception as e:
                    print(f"Error removing file {file}: {e}")

    print(f"\nTotal images removed: {removed_count}")


def main():
    # Check if ROOT_DIR exists
    if not os.path.isdir(ROOT_DIR):
        print(f"Error: The specified ROOT_DIR does not exist: {ROOT_DIR}")
        return

    remove_small_num_imgs_posts(ROOT_DIR, MIN_IMAGES_THRESHOLD)
    print("\nSingle-image post removal completed successfully.")


if __name__ == "__main__":
    main()
