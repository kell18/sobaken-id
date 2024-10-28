import os
import sys

# ----------------------------- Configuration -----------------------------

# Path to the directory containing the files
TARGET_DIR = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/test'

# ---------------------------------------------------------------------------

def remove_delim_files(target_dir):
    """
    Removes all files in the specified directory that end with 'DELIM.<extension>'.

    Args:
        target_dir (str): Path to the target directory.
    """
    if not os.path.isdir(target_dir):
        print(f"Error: The specified directory does not exist: {target_dir}")
        return

    # List all items in the directory
    all_items = os.listdir(target_dir)
    files_removed = 0

    for item in all_items:
        item_path = os.path.join(target_dir, item)

        # Proceed only if it's a file
        if os.path.isfile(item_path):
            # Split the filename and extension
            filename, ext = os.path.splitext(item)

            # Check if filename ends with 'DELIM' (case-sensitive)
            if filename.endswith('DELIM'):
                try:
                    os.remove(item_path)
                    files_removed += 1
                    print(f"Deleted: {item}")
                except Exception as e:
                    print(f"Error deleting file {item}: {e}")

    print(f"\nTotal files deleted: {files_removed}")

def main():
    # Optionally, allow the target directory to be passed as a command-line argument
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = TARGET_DIR

    remove_delim_files(target_dir)

if __name__ == "__main__":
    main()
