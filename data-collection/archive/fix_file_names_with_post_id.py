import json
import os
import sys
from collections import defaultdict


def fix_file_names_with_post_id(index_filename, base_imgs_path):
    """
    Renames files from random hashes to the known format of short-public-id_post-id_image-num
    """
    # Read the index file
    with open(index_filename, 'r', encoding='utf-8') as f:
        data = f.read()

    # Try to parse as JSON array
    try:
        entries = json.loads(data)
    except json.JSONDecodeError:
        # Assume JSON Lines format
        entries = []
        with open(index_filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {e}", file=sys.stderr)

    # Group entries by post_id
    entries_by_post_id = defaultdict(list)
    for entry in entries:
        post_id = entry.get('post_id')
        if post_id is None:
            continue
        entries_by_post_id[post_id].append(entry)

    # Process each post_id group
    for post_id, post_entries in entries_by_post_id.items():
        # Enumerate images for this post_id
        for idx, entry in enumerate(post_entries, start=1):
            photo = entry.get('photo')
            if not photo:
                continue
            local_filename = photo.get('local_filename')
            if not local_filename:
                continue
            new_filename = f"{post_id}_{idx}.jpg"
            old_path = os.path.join(base_imgs_path, local_filename)
            new_path = os.path.join(base_imgs_path, new_filename)
            # Check if source file exists
            if not os.path.exists(old_path):
                print(f"File {local_filename} does not exist, skipping.", file=sys.stderr)
                continue
            # Rename the file
            try:
                os.rename(old_path, new_path)
                print(f"Renamed {local_filename} to {new_filename}")
            except Exception as e:
                print(f"Error renaming {local_filename} to {new_filename}: {e}", file=sys.stderr)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Invalid arguments, usage: python rename_files.py /path/to/index.json /path/to/imgs/root")
        sys.exit(1)
    index_filename = sys.argv[1]
    base_imgs_path = sys.argv[2]
    fix_file_names_with_post_id(index_filename, base_imgs_path)
