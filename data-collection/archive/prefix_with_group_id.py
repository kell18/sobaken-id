import os
import sys
from pathlib import Path
from sys import prefix

directory_path = "/Users/albert.bikeev/Projects/sobaken-id/data/raw/raw_dedup_clean_dom_lapkin_1-3"
prefix = 'vkg187961884_'


def rename_files(directory, prefix):
    """
    Renames all files in the specified directory by prefixing them with prefix.

    Args:
        directory (str): The path to the directory containing the files to rename.
    """
    path = Path(directory)

    if not path.is_dir():
        print(f"Error: The path '{directory}' is not a valid directory.")
        return

    files = list(path.iterdir())
    total_files = len(files)
    renamed_count = 0
    skipped_count = 0

    print(f"Starting to rename {total_files} files in '{directory}'...\n")

    for idx, file in enumerate(files, start=1):
        if file.is_file():
            original_name = file.name
            new_name = f"{prefix}{original_name}"
            new_file = file.with_name(new_name)

            if new_file.exists():
                print(f"[{idx}/{total_files}] Skipping '{original_name}': '{new_name}' already exists.")
                skipped_count += 1
                continue

            try:
                file.rename(new_file)
                print(f"[{idx}/{total_files}] Renamed: '{original_name}' -> '{new_name}'")
                renamed_count += 1
            except Exception as e:
                print(f"[{idx}/{total_files}] Error renaming '{original_name}': {e}")
                skipped_count += 1

    print("\nRenaming completed.")
    print(f"Total files processed: {total_files}")
    print(f"Successfully renamed: {renamed_count}")
    print(f"Skipped/Failed: {skipped_count}")


if __name__ == "__main__":
    rename_files(directory_path, prefix)