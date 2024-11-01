import os
import shutil
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import json
import multiprocessing
from functools import partial
import textwrap
from file_name_info import FileNameInfo
from tqdm import tqdm  # Added for progress tracking

#### Docs:
# Adds an image with a post text on a noticable color after each post so marking up is easier:
# 1. You see where a post ends and a new starts
# 2. You can quickly distingluish if there is only 1 animal or more on each post by glancing over the text

# ----------------------------- Configuration -----------------------------

# Paths to the directories containing the images
ROOT_DIRS = [
    '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/_part_10'
]

# Path to the index file containing post texts
INDEX_FILE = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts_dedup/orig_index_tmpl.json'

# Path to a TrueType font file (.ttf)
FONT_PATH = '/Users/albert.bikeev/Projects/sobaken-id-assets/utils/JetBrainsMono-Bold.ttf'

# Number of group delimiters to insert after each GROUP_ID
NUM_GROUP_DELIMITERS = 5

# Image dimensions
IMAGE_WIDTH, IMAGE_HEIGHT = 800, 500

# Background color for delimiter images (dark green)
DELIMITER_BG_COLOR = (0, 85, 0)  # RGB values

# Text color for delimiter images
DELIMITER_TEXT_COLOR = (255, 255, 255)  # White

# Padding around the text (left, top, right, bottom)
PADDING = (50, 50, 50, 50)

# Font size range for the post text
MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 100

# Number of worker processes for multiprocessing
NUM_WORKERS = multiprocessing.cpu_count()

SUPPORTED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png']

# ---------------------------------------------------------------------------

# Global font cache to be used by each worker process
font_cache = {}

def init_pool():
    """
    Initializer for each worker process in the multiprocessing pool.
    Initializes the global font_cache as an empty dictionary.
    """
    global font_cache
    font_cache = {}

def load_post_texts():
    """
    Loads post texts from the index file.

    Returns:
        dict: Mapping from (group_id, post_id) to post text.
    """
    post_texts = {}
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    try:
                        post = json.loads(line)
                        group_id = str(post.get('group_id')).replace('-', '')
                        post_id = str(post.get('post_id')).replace('-', '')
                        if group_id and post_id:
                            # Create unique post identifier
                            key = (group_id, post_id)
                            txt = post.get('text', '')
                            # Truncate text to first 250 and last 200 characters
                            if len(txt) > 450:
                                truncated_text = f"{txt[:250]} ... {txt[-200:]}"
                            else:
                                truncated_text = txt
                            post_texts[key] = truncated_text
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON line: {e}")
        print("Post texts loaded.")
    else:
        print(f"No index file found at {INDEX_FILE}. Post texts will be empty.")
        post_texts = {}
    return post_texts

def generate_delimiter_image(post_text, output_path):
    """
    Generates an image with the post text on a dark green background.
    The text is dynamically wrapped and scaled to utilize the full image dimensions.

    Args:
        post_text (str): The text to display on the image.
        output_path (str): The path to save the generated image.
    """

    global font_cache  # Use the global font_cache

    # Create a new image with the specified background color
    image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=DELIMITER_BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Define the area where text can be drawn
    text_area_width = IMAGE_WIDTH - PADDING[0] - PADDING[2]
    text_area_height = IMAGE_HEIGHT - PADDING[1] - PADDING[3]

    # Function to wrap text based on current font size using textwrap
    def wrap_text(text, font, max_width):
        wrapper = textwrap.TextWrapper(width=100)  # Initial width
        lines = []
        words = text.replace('\n', ' ').split()
        if not words:
            return lines
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            if test_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines

    # Determine the optimal font size
    optimal_font_size = MAX_FONT_SIZE
    wrapped_lines = []
    total_text_height = 0
    while optimal_font_size >= MIN_FONT_SIZE:
        if optimal_font_size in font_cache:
            font = font_cache[optimal_font_size]
        else:
            try:
                font = ImageFont.truetype(FONT_PATH, size=optimal_font_size)
                font_cache[optimal_font_size] = font
            except IOError:
                print(f"Font file not found at {FONT_PATH}. Using default font.")
                font = ImageFont.load_default()
                font_cache[optimal_font_size] = font
        wrapped_lines = wrap_text(post_text, font, text_area_width)
        # Calculate total height
        total_text_height = 0
        for line in wrapped_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_height = bbox[3] - bbox[1]
            total_text_height += line_height + 10  # 10 pixels between lines
        if total_text_height <= text_area_height:
            break
        optimal_font_size -= 2  # Decrease font size and try again

    if optimal_font_size < MIN_FONT_SIZE:
        print(f"Warning: Text may not fit well within the delimiter image at size {optimal_font_size}.")

    # Calculate starting y position
    y_text = PADDING[1] + (text_area_height - total_text_height) // 2

    # Draw each line of text
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x_text = PADDING[0] + (text_area_width - text_width) // 2
        draw.text((x_text, y_text), line, font=font, fill=DELIMITER_TEXT_COLOR)
        y_text += text_height + 10  # Move to the next line

    # Save the image with optimized quality
    image.save(
        output_path,
        format='JPEG',
        quality=30,       # Lower quality for smaller file size
        optimize=True     # Enable optimization
        # method=6         # Optional for WebP
    )
    # Uncomment the following line to enable save confirmations
    # print(f"Delimiter image saved to {output_path}")

def process_post_delimiter(args):
    """
    Worker function to generate a post delimiter image.

    Args:
        args (tuple): Contains (group_id, post_id, post_text, root_dir)

    Returns:
        int: 1 if successful, 0 otherwise.
    """
    group_id, post_id, post_text, root_dir = args  # Removed font_cache from args
    delimiter_filename = f"vkg{group_id}_{post_id}_DELIM.jpg"
    delimiter_destination = os.path.join(root_dir, delimiter_filename)
    try:
        generate_delimiter_image(post_text, delimiter_destination)
        return 1
    except Exception as e:
        print(f"Error generating delimiter {delimiter_filename}: {e}")
        return 0

def process_group_delimiter(args):
    """
    Worker function to generate a group delimiter image.

    Args:
        args (tuple): Contains (group_id, i, root_dir)

    Returns:
        int: 1 if successful, 0 otherwise.
    """
    group_id, i, root_dir = args  # Removed font_cache from args
    group_delim_filename = f"vkg{group_id}_GROUP_{i}_DELIM.jpg"
    group_delim_destination = os.path.join(root_dir, group_delim_filename)
    try:
        group_text = f"Group {group_id}"
        generate_delimiter_image(group_text, group_delim_destination)
        return 1
    except Exception as e:
        print(f"Error generating group delimiter {group_delim_filename}: {e}")
        return 0

def insert_post_delimiters(groups, post_texts):
    """
    Inserts delimiter images for each post, generated from the post text.

    Args:
        groups (dict): Dictionary with keys as (GROUP_ID, POST_ID) and values as lists of (root_dir, filename).
        post_texts (dict): Mapping from (group_id, post_id) to post text.

    Returns:
        int: Number of delimiters inserted.
    """
    tasks = []
    for (group_id, post_id), files in groups.items():
        post_text = post_texts.get((group_id, post_id), 'No text available')
        root_dir = files[0][0]  # Get the root_dir from the first file
        tasks.append((group_id, post_id, post_text, root_dir))

    inserted_count = 0
    total_tasks = len(tasks)
    with multiprocessing.Pool(processes=NUM_WORKERS, initializer=init_pool) as pool:
        # Using tqdm for progress tracking
        for result in tqdm(pool.imap_unordered(process_post_delimiter, tasks), total=total_tasks, desc="Processing post delimiters"):
            inserted_count += result
    return inserted_count

def insert_group_delimiters(groups, num_delimiters):
    """
    Inserts a specified number of group delimiter images after each GROUP_ID.

    Args:
        groups (dict): Dictionary with keys as (GROUP_ID, POST_ID) and values as lists of (root_dir, filename).
        num_delimiters (int): Number of group delimiters to insert per GROUP_ID.

    Returns:
        int: Total number of group delimiters inserted.
    """
    tasks = []
    # Organize groups by GROUP_ID
    groups_by_group = defaultdict(list)
    group_root_dirs = {}
    for (group_id, post_id), files in groups.items():
        groups_by_group[group_id].append(post_id)
        group_root_dirs[group_id] = files[0][0]  # Get root_dir from first file

    for group_id, post_ids in groups_by_group.items():
        root_dir = group_root_dirs[group_id]
        for i in range(1, num_delimiters + 1):
            tasks.append((group_id, i, root_dir))

    inserted_count = 0
    total_tasks = len(tasks)
    with multiprocessing.Pool(processes=NUM_WORKERS, initializer=init_pool) as pool:
        # Using tqdm for progress tracking
        for result in tqdm(pool.imap_unordered(process_group_delimiter, tasks), total=total_tasks, desc="Processing group delimiters"):
            inserted_count += result
    return inserted_count

def main():
    # Check if all ROOT_DIRS exist
    for dir_path in ROOT_DIRS:
        if not os.path.isdir(dir_path):
            print(f"Error: The specified directory does not exist: {dir_path}")
            return

    # Load post texts
    post_texts = load_post_texts()

    # Step 1: Scan the directories and group files by (GROUP_ID, POST_ID)
    groups = defaultdict(list)
    for root_dir in ROOT_DIRS:
        # List all files in the directory
        all_files = [f for f in os.listdir(root_dir) if any([ex for ex in SUPPORTED_IMAGE_EXTENSIONS if f.endswith(ex)])]
        for filename in all_files:
            filepath = os.path.join(root_dir, filename)
            if os.path.isfile(filepath):
                file_info = FileNameInfo.from_full_path(filename)
                group_id, post_id = file_info.group_id, file_info.post_id
                if group_id and post_id:
                    # Store the root_dir along with the filename
                    groups[(group_id, post_id)].append((root_dir, filename))
                else:
                    print(f"Skipping file with unexpected format: {filename}")

    print(f"\nTotal unique posts found: {len(groups)}")

    # Step 2: Insert post delimiter images
    print("Inserting post delimiter images for posts...")
    inserted_posts = insert_post_delimiters(groups, post_texts)
    print(f"Total post delimiters inserted: {inserted_posts}\n")

    # Step 3: Insert group delimiter images
    print(f"Inserting {NUM_GROUP_DELIMITERS} group delimiters after each GROUP_ID...")
    inserted_groups = insert_group_delimiters(groups, NUM_GROUP_DELIMITERS)
    print(f"Total group delimiters inserted: {inserted_groups}\n")

    print("Processing completed successfully.")

if __name__ == "__main__":
    main()
