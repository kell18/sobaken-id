import os
import json
from pathlib import Path
import logging

# ----------------------------- Docs -----------------------------
"""
script that will get all the group and post IDs within specific directory, and, given the index.json file, 
will produce a smaller index.json with only group and post ID, post text and from_id
"""


# ----------------------------- Configuration -----------------------------

# Define the paths here
IMAGE_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_10'
ORIGINAL_INDEX_PATH = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/index.json'
OUTPUT_INDEX_PATH = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/txt_index_part10.json'
FILE_EXTENSION = 'jpg'

# ----------------------------- Setup Logging -----------------------------

# Configure logging to display messages with severity INFO and above
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ----------------------------- Helper Functions -----------------------------

def extract_ids_from_filename(filename):
    """
    Extracts group_id and post_id from the filename.

    Args:
        filename (str): The image filename.

    Returns:
        tuple: (group_id, post_id) if pattern matches, else (None, None)
    """
    basename, _ = os.path.splitext(filename)
    if not basename.startswith('vkg'):
        logging.warning(f"Filename '{filename}' does not start with 'vkg'. Skipping.")
        return (None, None)

    try:
        # Remove 'vkg' prefix
        basename = basename[3:]
        parts = basename.split('_')
        if len(parts) < 3:
            logging.warning(f"Filename '{filename}' does not have enough parts. Skipping.")
            return (None, None)
        group_id = parts[0]
        post_id = parts[1]
        return (group_id, post_id)
    except Exception as e:
        logging.error(f"Error extracting IDs from filename '{filename}': {e}")
        return (None, None)

def collect_unique_ids(directory, file_extension='jpg'):
    """
    Scans the directory and collects unique (group_id, post_id) pairs.

    Args:
        directory (str): Path to the directory containing image files.
        file_extension (str): Extension of image files to consider.

    Returns:
        set: A set of tuples containing (group_id, post_id).
    """
    unique_ids = set()
    supported_extensions = [f".{file_extension.lower()}", f".{file_extension.upper()}"]

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in supported_extensions):
                group_id, post_id = extract_ids_from_filename(file)
                if group_id and post_id:
                    unique_ids.add((group_id, post_id))
    logging.info(f"Collected {len(unique_ids)} unique (group_id, post_id) pairs from '{directory}'.")
    return unique_ids

def filter_index_json(original_index_path, output_index_path, target_ids, json_format='array'):
    """
    Filters the original index.json to include only entries matching target_ids.

    Args:
        original_index_path (str): Path to the original index.json file.
        output_index_path (str): Path to save the filtered index.json.
        target_ids (set): Set of (group_id, post_id) tuples to retain.
        json_format (str): 'lines' for JSON Lines, 'array' for JSON Array.
    """
    filtered_entries = []
    skipped_entries = 0

    if json_format == 'lines':
        with open(original_index_path, 'r', encoding='utf-8') as infile:
            for line_number, line in enumerate(infile, 1):
                try:
                    entry = json.loads(line)
                    group_id = str(entry.get('group_id', '')).replace('-', '')
                    post_id = str(entry.get('post_id', '')).replace('-', '')
                    if (group_id, post_id) in target_ids:
                        # Extract only the required fields
                        filtered_entry = {
                            'group_id': group_id,
                            'post_id': post_id,
                            'post_text': entry.get('text', ''),
                            'from_id': entry.get('from_id', '')
                        }
                        filtered_entries.append(filtered_entry)
                except json.JSONDecodeError as jde:
                    logging.error(f"JSON decode error in line {line_number}: {jde}. Skipping line.")
                    skipped_entries += 1
                except Exception as e:
                    logging.error(f"Unexpected error in line {line_number}: {e}. Skipping line.")
                    skipped_entries += 1
    elif json_format == 'array':
        with open(original_index_path, 'r', encoding='utf-8') as infile:
            try:
                data = json.load(infile)
                for entry in data:
                    group_id = str(entry.get('group_id', '')).replace('-', '')
                    post_id = str(entry.get('post_id', '')).replace('-', '')
                    if (group_id, post_id) in target_ids:
                        # Extract only the required fields
                        filtered_entry = {
                            'group_id': group_id,
                            'post_id': post_id,
                            'post_text': entry.get('post_text', ''),
                            'from_id': entry.get('from_id', '')
                        }
                        filtered_entries.append(filtered_entry)
            except json.JSONDecodeError as jde:
                logging.error(f"JSON decode error: {jde}. Exiting.")
                return
            except Exception as e:
                logging.error(f"Unexpected error: {e}. Exiting.")
                return
    else:
        logging.error(f"Unsupported JSON format: {json_format}. Use 'lines' or 'array'.")
        return

    logging.info(f"Filtered {len(filtered_entries)} entries. Skipped {skipped_entries} entries due to errors.")

    # Write to the new index.json
    if json_format == 'lines':
        with open(output_index_path, 'w', encoding='utf-8') as outfile:
            for entry in filtered_entries:
                json.dump(entry, outfile, ensure_ascii=False)
                outfile.write('\n')
    elif json_format == 'array':
        with open(output_index_path, 'w', encoding='utf-8') as outfile:
            json.dump(filtered_entries, outfile, ensure_ascii=False, indent=4)

    logging.info(f"Successfully wrote filtered index to '{output_index_path}'.")

def detect_json_format(index_path):
    """
    Detects whether the JSON file is in lines or array format.

    Args:
        index_path (str): Path to the index.json file.

    Returns:
        str: 'lines' or 'array'
    """
    with open(index_path, 'r', encoding='utf-8') as infile:
        first_char = infile.read(1)
        if first_char == '[':
            return 'array'
        else:
            return 'lines'

# ----------------------------- Main Execution -----------------------------

def main():
    # Validate paths
    if not os.path.isdir(IMAGE_DIR):
        logging.error(f"Image directory '{IMAGE_DIR}' does not exist.")
        return
    if not os.path.isfile(ORIGINAL_INDEX_PATH):
        logging.error(f"Original index file '{ORIGINAL_INDEX_PATH}' does not exist.")
        return

    # Detect JSON format
    json_format = detect_json_format(ORIGINAL_INDEX_PATH)
    logging.info(f"Detected JSON format: {json_format}")

    # Step 1: Collect unique (group_id, post_id) pairs from image filenames
    target_ids = collect_unique_ids(IMAGE_DIR, file_extension=FILE_EXTENSION)

    if not target_ids:
        logging.error("No valid (group_id, post_id) pairs found. Exiting.")
        return

    # Step 2: Filter the original index.json
    filter_index_json(ORIGINAL_INDEX_PATH, OUTPUT_INDEX_PATH, target_ids, json_format=json_format)

if __name__ == '__main__':
    main()
