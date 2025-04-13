import os
import shutil
import re
from pathlib import Path
from tqdm import tqdm

# ============================
# Configuration
# ============================

# directory containing '_part_<N>' folders
source_root_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup'
target_root_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_per_group2'

# Compile regular expressions for filename patterns
ignore_pattern = re.compile(r'^vkg\d+_GROUP_\d+_DELIM\.jpg$')
process_pattern = re.compile(r'^vkg(?P<group_id>\d+)_(?P<post_id>\d+)_(?P<img_num>.+)\.jpg$')

move_or_copy = 'copy'

part_prefix = '_part_'

# ============================
# Main
# ============================

if __name__ == '__main__':
    Path(target_root_dir).mkdir(parents=True, exist_ok=True)
    # Iterate over all '_part_<N>' directories in the source root directory
    dir_paths = [d.path for d in os.scandir(source_root_dir) if d.is_dir() and d.name.startswith(part_prefix)]
    for part_dir in tqdm(dir_paths, f'Processing {part_prefix}N parts', total=len(dir_paths)):
        # Iterate over all files in the current '_part_<N>' directory
        for file_entry in os.scandir(part_dir):
            if file_entry.is_file():
                filename = file_entry.name

                # Check if the file matches the ignore pattern
                if ignore_pattern.match(filename):
                    # Ignore group delimiter files
                    continue
                else:
                    # Check if the file matches the process pattern
                    match = process_pattern.match(filename)
                    if match:
                        group_id = match.group('group_id')

                        # Build the target directory path for the current group
                        target_dir = os.path.join(target_root_dir, f'vkg{group_id}')
                        os.makedirs(target_dir, exist_ok=True)

                        # Move the file to the target directory
                        src_file = file_entry.path
                        dst_file = os.path.join(target_dir, filename)
                        if move_or_copy == 'move':
                            shutil.move(src_file, dst_file)
                        else:
                            shutil.copy(src_file, dst_file)
                    else:
                        # Print a message if the file doesn't match any pattern
                        print(f"File not recognized and will be ignored: {filename}")
