import os
import shutil

def flatten_directory(root_dir):
    """
    Moves all files from immediate subdirectories of root_dir into root_dir.

    Parameters:
    root_dir (str): The path to the root directory.
    """
    # Ensure the root directory exists
    if not os.path.isdir(root_dir):
        raise ValueError(f"The specified root directory does not exist: {root_dir}")

    # Iterate over each item in the root directory
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)

        # Check if the item is a directory
        if os.path.isdir(item_path):
            # Iterate over each file in the subdirectory
            for filename in os.listdir(item_path):
                file_path = os.path.join(item_path, filename)

                # Ensure it's a file (not a subdirectory)
                if os.path.isfile(file_path):
                    destination = os.path.join(root_dir, filename)

                    # Move the file to the root directory
                    shutil.move(file_path, destination)
                    print(f"Moved: {file_path} --> {destination}")

            # Optionally, remove the empty subdirectory
            try:
                os.rmdir(item_path)
                print(f"Removed empty directory: {item_path}")
            except OSError:
                print(f"Directory not empty, could not remove: {item_path}")

    print("Flattening complete.")

if __name__ == "__main__":
    # Replace '/path/to/root' with the actual path to your root directory
    root_directory = '/Users/albert.bikeev/Projects/sobaken-id/data/clean_dom_lapkin_1-3_flat/train'
    flatten_directory(root_directory)