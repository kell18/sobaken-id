import os
import json
from tqdm import tqdm

# Set the paths
input_json_file = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/index.json'
output_json_file = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/index_dedup.json'
images_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/imgs_dedup'


def filter_index_json(input_json_path, output_json_path, images_directory):
    """
    Filters the index.json file to include only records where at least one 'photo' has a 'local_filename'
    that exists in the specified images_directory. Within each record, removes 'photo' entries
    that do not have corresponding image files. If a record has no 'photo' entries left after filtering,
    it is excluded from the output.

    Parameters:
    - input_json_path (str): Path to the original index.json file (JSON Lines format).
    - output_json_path (str): Path to save the filtered index.json file.
    - images_directory (str): Directory where image files are stored.
    """
    # Step 1: Gather all existing filenames in images_directory
    print("Scanning images directory to build a set of existing filenames...")
    existing_filenames = set()
    for root, dirs, files in os.walk(images_directory):
        for file in files:
            existing_filenames.add(file)
    print(f"Total unique image filenames found: {len(existing_filenames)}\n")

    # Initialize counters
    total_records = 0
    records_with_photos = 0
    records_kept = 0
    records_removed = 0
    total_photos = 0
    photos_kept = 0
    photos_removed = 0

    # Step 2: Open input and output files
    print("Starting to process index.json...")
    with open(input_json_path, 'r', encoding='utf-8') as infile, \
            open(output_json_path, 'w', encoding='utf-8') as outfile:

        # Initialize a progress bar
        for line in tqdm(infile, desc="Processing records"):
            total_records += 1
            stripped_line = line.strip()

            # Skip empty lines
            if not stripped_line:
                records_removed += 1
                continue

            # Attempt to parse the JSON record
            try:
                record = json.loads(stripped_line)
            except json.JSONDecodeError:
                records_removed += 1
                continue  # Skip invalid JSON lines

            # Extract 'photos' array
            photos = record.get('photos', [])
            if not isinstance(photos, list):
                records_removed += 1
                continue  # Skip records where 'photos' is not a list

            if not photos:
                records_removed += 1
                continue  # Skip records with empty 'photos'

            records_with_photos += 1
            total_photos += len(photos)

            # Filter photos based on existence of 'local_filename'
            filtered_photos = []
            for photo in photos:
                local_filename = photo.get('local_filename')
                if not local_filename:
                    photos_removed += 1
                    continue  # Skip photos without 'local_filename'

                if local_filename in existing_filenames:
                    filtered_photos.append(photo)
                    photos_kept += 1
                else:
                    photos_removed += 1

            # If no photos remain after filtering, skip the record
            if not filtered_photos:
                records_removed += 1
                continue

            # Update the record with filtered photos
            record['photos'] = filtered_photos
            records_kept += 1

            # Write the updated record to the output file
            outfile.write(json.dumps(record, ensure_ascii=False) + '\n')

    # Step 3: Print summary
    print("\nFiltering complete.\n")
    print(f"Total records processed: {total_records}")
    print(f"Records with photos: {records_with_photos}")
    print(f"Records kept: {records_kept}")
    print(f"Records removed: {records_removed}")
    print(f"\nTotal photos evaluated: {total_photos}")
    print(f"Photos kept: {photos_kept}")
    print(f"Photos removed: {photos_removed}\n")
    print(f"Filtered index saved to: {output_json_path}")


if __name__ == "__main__":
    filter_index_json(input_json_file, output_json_file, images_dir)
