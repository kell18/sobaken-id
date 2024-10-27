import os
import shutil
import re
from collections import defaultdict

# Configuration
ROOT_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/imgs_dedup'
OUTPUT_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts'
NUM_PARTS = 10

def split_dataset(root_dir, output_dir, num_parts):
    # Step 1: Create output directories
    part_dirs = [os.path.join(output_dir, f'part_{i+1}') for i in range(num_parts)]
    for dir_path in part_dirs:
        os.makedirs(dir_path, exist_ok=True)
    print(f"Created {num_parts} directories in '{output_dir}'.")

    # Step 2: Group files by POST_ID
    post_groups = defaultdict(list)
    total_files = 0
    for filename in os.listdir(root_dir):
        if os.path.isfile(os.path.join(root_dir, filename)):
            parts = filename.split('_')
            if len(parts) < 3:
                print(f"Skipping file with unexpected format: {filename}")
                continue
            post_id = parts[1]
            post_groups[post_id].append(filename)
            total_files += 1
    print(f"Total unique POST_IDs: {len(post_groups)}")
    print(f"Total files to process: {total_files}")

    # Step 3: Sort POST_IDs by number of files (descending) for balanced distribution
    sorted_posts = sorted(post_groups.values(), key=len, reverse=True)

    # Initialize counts for each part
    part_counts = [0] * num_parts
    assignments = [[] for _ in range(num_parts)]

    # Step 4: Assign each group to the part with the least number of files
    for group in sorted_posts:
        min_index = part_counts.index(min(part_counts))
        assignments[min_index].extend(group)
        part_counts[min_index] += len(group)

    # Step 5: Copy files to respective directories
    for i, part in enumerate(assignments):
        part_dir = part_dirs[i]
        for filename in part:
            src_path = os.path.join(root_dir, filename)
            dest_path = os.path.join(part_dir, filename)
            shutil.copy2(src_path, dest_path)
        print(f"Part {i+1}: {len(part)} files copied to '{part_dir}'.")

    print("Dataset splitting completed successfully.")

if __name__ == "__main__":
    split_dataset(ROOT_DIR, OUTPUT_DIR, NUM_PARTS)