import os
import shutil
from collections import defaultdict

# ----------------------------- Configuration -----------------------------

# Path to the directory containing the images
ROOT_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/part_10'

# Path to the reference delimiter image
POST_DELIM_IMAGE_PATH = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/DELIM.png'
_, POST_DELIM_EXT = os.path.splitext(os.path.basename(POST_DELIM_IMAGE_PATH))
GROUP_DELIM_IMAGE_PATH = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/GROUP_DELIM.jpg'
_, GROUP_DELIM_EXT = os.path.splitext(os.path.basename(GROUP_DELIM_IMAGE_PATH))


# Number of group delimiters to insert after each GROUP_ID
NUM_GROUP_DELIMITERS = 5

# ---------------------------------------------------------------------------

def extract_ids(filename):
    """
    Extracts GROUP_ID and POST_ID from the filename.

    Expected filename format: vkg<GROUP_ID>_<POST_ID>_<IMG_NUM>.jpg
    Example: vkg123_456_1.jpg
    """
    basename = os.path.basename(filename)
    name, ext = os.path.splitext(basename)
    parts = name.split('_')
    if len(parts) != 3:
        return None, None
    group_part = parts[0]
    post_id = parts[1]

    # Extract GROUP_ID by removing the 'vkg' prefix
    if group_part.startswith('vkg'):
        group_id = group_part[3:]
    else:
        return None, None

    return group_id, post_id

def remove_single_image_posts(groups):
    """
    Removes images belonging to posts that have only one image.

    Args:
        groups (dict): Dictionary with keys as (GROUP_ID, POST_ID) and values as lists of filenames.

    Returns:
        int: Number of images removed.
    """
    removed_count = 0
    for (group_id, post_id), files in groups.items():
        if len(files) == 1:
            file_to_remove = os.path.join(ROOT_DIR, files[0])
            try:
                os.remove(file_to_remove)
                removed_count += 1
                print(f"Removed single-image post: {files[0]}")
            except Exception as e:
                print(f"Error removing file {files[0]}: {e}")
    return removed_count

def insert_post_delimiters(groups):
    """
    Inserts delimiter images for each post that has more than one image.

    Args:
        groups (dict): Dictionary with keys as (GROUP_ID, POST_ID) and values as lists of filenames.

    Returns:
        int: Number of delimiters inserted.
    """
    inserted_count = 0
    for (group_id, post_id), files in groups.items():
        if len(files) > 1:
            delimiter_filename = f"vkg{group_id}_{post_id}_DELIM{POST_DELIM_EXT}"
            delimiter_destination = os.path.join(ROOT_DIR, delimiter_filename)
            try:
                shutil.copy2(POST_DELIM_IMAGE_PATH, delimiter_destination)
                inserted_count += 1
                print(f"Inserted post delimiter: {delimiter_filename}")
            except Exception as e:
                print(f"Error inserting delimiter {delimiter_filename}: {e}")
    return inserted_count

def insert_group_delimiters(groups, num_delimiters):
    """
    Inserts a specified number of group delimiter images after each GROUP_ID.

    Args:
        groups (dict): Dictionary with keys as (GROUP_ID, POST_ID) and values as lists of filenames.
        num_delimiters (int): Number of group delimiters to insert per GROUP_ID.

    Returns:
        int: Total number of group delimiters inserted.
    """
    inserted_count = 0
    # Organize groups by GROUP_ID
    groups_by_group = defaultdict(list)
    for (group_id, post_id), files in groups.items():
        groups_by_group[group_id].append(post_id)

    for group_id, post_ids in groups_by_group.items():
        # Sort post_ids to maintain a consistent order (optional)
        post_ids_sorted = sorted(post_ids)
        for post_id in post_ids_sorted:
            # Post delimiters are already inserted
            pass  # No action needed here

        # After all posts of the current GROUP_ID, insert group delimiters
        for i in range(1, num_delimiters + 1):
            group_delim_filename = f"vkg{group_id}_GROUP_{i}_DELIM{GROUP_DELIM_EXT}"
            group_delim_destination = os.path.join(ROOT_DIR, group_delim_filename)
            try:
                shutil.copy2(GROUP_DELIM_IMAGE_PATH, group_delim_destination)
                inserted_count += 1
                print(f"Inserted group delimiter: {group_delim_filename}")
            except Exception as e:
                print(f"Error inserting group delimiter {group_delim_filename}: {e}")

    return inserted_count

def main():
    # Check if ROOT_DIR exists
    if not os.path.isdir(ROOT_DIR):
        print(f"Error: The specified ROOT_DIR does not exist: {ROOT_DIR}")
        return

    # Check if DELIM_IMAGE_PATH exists
    if not os.path.isfile(POST_DELIM_IMAGE_PATH) or not os.path.isfile(GROUP_DELIM_IMAGE_PATH):
        print(f"Error: The delimiter image does not exist: {POST_DELIM_IMAGE_PATH} or {GROUP_DELIM_IMAGE_PATH}")
        return

    # Step 1: Scan the directory and group files by (GROUP_ID, POST_ID)
    groups = defaultdict(list)
    all_files = os.listdir(ROOT_DIR)

    for filename in all_files:
        filepath = os.path.join(ROOT_DIR, filename)
        if os.path.isfile(filepath):
            group_id, post_id = extract_ids(filename)
            if group_id and post_id:
                groups[(group_id, post_id)].append(filename)
            else:
                print(f"Skipping file with unexpected format: {filename}")

    print(f"\nTotal unique posts found: {len(groups)}")

    # Step 2: Remove single-image posts
    print("\nRemoving single-image posts...")
    removed = remove_single_image_posts(groups)
    print(f"Total single-image posts removed: {removed}\n")

    # After removal, rebuild the groups dictionary to exclude removed posts
    updated_groups = defaultdict(list)
    remaining_files = os.listdir(ROOT_DIR)

    for filename in remaining_files:
        filepath = os.path.join(ROOT_DIR, filename)
        if os.path.isfile(filepath):
            group_id, post_id = extract_ids(filename)
            if group_id and post_id:
                # Only include posts with more than one image
                if len(groups.get((group_id, post_id), [])) > 1:
                    updated_groups[(group_id, post_id)].append(filename)

    # Step 3: Insert post delimiter images
    print("Inserting post delimiter images for qualifying posts...")
    inserted_posts = insert_post_delimiters(updated_groups)
    print(f"Total post delimiters inserted: {inserted_posts}\n")

    # Step 4: Insert group delimiter images
    print(f"Inserting {NUM_GROUP_DELIMITERS} group delimiters after each GROUP_ID...")
    inserted_groups = insert_group_delimiters(updated_groups, NUM_GROUP_DELIMITERS)
    print(f"Total group delimiters inserted: {inserted_groups}\n")

    print("Processing completed successfully.")

if __name__ == "__main__":
    main()