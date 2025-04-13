import json
import os

input_file = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/index.json'
output_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/group_based_indexes'

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

output_files = {}

def main():
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Remove any leading/trailing whitespace
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                group_id = data.get('group_id')
                if group_id is None:
                    continue  # Skip if group_id is missing

                # Open the output file for this group_id, if not already opened
                if group_id not in output_files:
                    output_filename = os.path.join(output_dir, f'group_{group_id}.json')
                    output_files[group_id] = open(output_filename, 'w', encoding='utf-8')

                # Write the line to the corresponding output file
                output_files[group_id].write(line + '\n')

            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line}")

    # Close all output files
    for f in output_files.values():
        f.close()

if __name__ == '__main__':
    main()
