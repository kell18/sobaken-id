import os
import shutil

# Configuration
ROOT_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/deduplicated_imgs'
OUTPUT_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup'
NUM_PARTS = 10

def split_dataset(root_dir, output_dir, num_parts):
    # Step 1: Create output directories
    part_dirs = [os.path.join(output_dir, f'_part_{i+1}') for i in range(num_parts)]
    for dir_path in part_dirs:
        os.makedirs(dir_path, exist_ok=True)
    print(f"Created {num_parts} directories in '{output_dir}'.")

    # Step 2: Collect all filenames and extract GROUP_ID and POST_ID
    post_files = {}
    total_files = 0
    for filename in os.listdir(root_dir):
        filepath = os.path.join(root_dir, filename)
        if os.path.isfile(filepath):
            parts = filename.split('_')
            if len(parts) < 3:
                print(f"Skipping file with unexpected format: {filename}")
                continue
            group_part = parts[0]
            post_id = parts[1]
            if not group_part.startswith('vkg'):
                print(f"Skipping file with unexpected format: {filename}")
                continue
            group_id = group_part[3:]  # Remove 'vkg' prefix
            key = (group_id, post_id)
            if key not in post_files:
                post_files[key] = []
            post_files[key].append(filename)
            total_files += 1
    print(f"Total unique posts (GROUP_ID, POST_ID): {len(post_files)}")
    print(f"Total files to process: {total_files}")

    # Step 3: Sort the posts by GROUP_ID and POST_ID (as strings)
    sorted_posts = sorted(post_files.items(), key=lambda x: (x[0][0], x[0][1]))

    # Step 4: Divide the sorted posts into NUM_PARTS parts
    num_posts = len(sorted_posts)
    posts_per_part = num_posts // num_parts
    extra = num_posts % num_parts  # Number of parts that will have one extra post

    assignments = [[] for _ in range(num_parts)]
    idx = 0
    for i in range(num_parts):
        end_idx = idx + posts_per_part + (1 if i < extra else 0)
        assigned_posts = sorted_posts[idx:end_idx]
        for key, files in assigned_posts:
            assignments[i].extend(files)
        idx = end_idx

    # Step 5: Copy files to respective directories
    for i, part in enumerate(assignments):
        part_dir = part_dirs[i]
        for filename in sorted(part):  # Ensure files are sorted within each part
            src_path = os.path.join(root_dir, filename)
            dest_path = os.path.join(part_dir, filename)
            shutil.copy2(src_path, dest_path)
        print(f"Part {i+1}: {len(part)} files copied to '{part_dir}'.")

    print("Dataset splitting completed successfully.")

if __name__ == "__main__":
    split_dataset(ROOT_DIR, OUTPUT_DIR, NUM_PARTS)
