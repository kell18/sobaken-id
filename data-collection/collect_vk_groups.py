import json
import asyncio
import aiohttp
import time
import os
from tqdm import tqdm
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VKGroup:
    id: str
    id_num: int
    city: str | None  # in Russian, None for non-city specific groups
    country2letter: str = 'ru'


# VK service token from environment variable
service_token = os.environ.get('VK_SERVICE_TOKEN')
if not service_token:
    logger.error("VK_SERVICE_TOKEN environment variable not set.")
    exit(1)

# List of VK groups to scrape
groups_to_search = [
    # VKGroup('poisk_ul', 34900407, 'Ульяновск'),
    # VKGroup('poteryha', 29426442, 'Барнаул'),
    # VKGroup('poteryashki_karelia', 83381493, 'Карелия'),
    # VKGroup('club81472745', 81472745, 'Казань'),
    # VKGroup('myhomeforpet', 133848717, 'Альметьевск'),
    # VKGroup('club30323533', 30323533, 'Краснодар'), ## <- низкое качество куча котят и щенков
    # VKGroup('sledopit.online', 198498843, None),
    # VKGroup('goodhandshelp', 42062020, None),
]

# Directory paths
imgs_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/imgs'  # All images will be saved here
scrape_params_file_p = '/Users/albert.bikeev/Projects/sobaken-id/data-collection/resources/parameters.json'
# Index and meta_info files in root directory
index_file_path = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/index.json'
meta_info_file_p = '/Users/albert.bikeev/Projects/sobaken-id/data/raw/vk_posts/metainfo.json'

# Attachment types to skip
attachment_types_to_skip = ['doc', 'video', 'link', 'audio']

# VK API and download settings
batch_size = 100  # Number of posts per request (max 100)
max_concurrent_image_downloads = 10  # Adjust based on network capabilities
vk_api_rate_limit = 3  # Max VK API requests per second

# Limit the number of posts per group
max_posts_per_group = 5000

# Default scrape parameters
default_parameters = {}

# Global meta_infos to collect meta information across groups
meta_infos = []


def extract_image(attachment_photo):
    if 'orig_photo' in attachment_photo:
        return attachment_photo['orig_photo']
    elif 'sizes' in attachment_photo and len(attachment_photo['sizes']) > 0:
        biggest_height_img = sorted(attachment_photo['sizes'], key=lambda a: a['height'], reverse=True)[0]
        return biggest_height_img
    else:
        return None


def construct_index_record(item, images, group_id):
    return {
        "group_id": group_id,
        "post_id": item['id'],
        "text": item['text'],
        "photos": images,
        "full_link": get_post_full_link(item['owner_id'], item['id']),
        "date_ts": item['date'],
        "from_id": item['from_id'],
    }


def append_index_record_to_file(index_record, full_file_path):
    with open(full_file_path, "a", encoding='utf-8') as myfile:
        record_str = json.dumps(index_record, ensure_ascii=False)
        myfile.write(record_str + '\n')


def get_post_full_link(the_owner_id, post_id):
    return f'https://vk.com/wall{the_owner_id}_{post_id}'


def get_latest_metainfo_from_file(metainfo_path):
    if not os.path.exists(metainfo_path):
        logger.warning(f"Meta info file does not exist at '{metainfo_path}'. Returning empty list.")
        return []
    try:
        with open(metainfo_path, 'r', encoding='utf-8') as f:
            meta_infos = json.load(f)
            logger.info(f"Successfully read meta info from '{metainfo_path}'.")
            return meta_infos
    except json.JSONDecodeError:
        logger.error(f"JSON decode error: The file '{metainfo_path}' contains invalid JSON.")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading '{metainfo_path}': {e}")
        return []

def get_latest_scrape_params_from_file(scrape_params_file_path, default_parameters):
    if os.path.exists(scrape_params_file_path):
        try:
            with open(scrape_params_file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("scrape_params_file is corrupted. Resetting to default parameters.")
            return default_parameters.copy()
    else:
        return default_parameters.copy()


def save_latest_scrape_params_to_file(scrape_params, scrape_params_file_path):
    with open(scrape_params_file_path, 'w') as f:
        json.dump(scrape_params, f)


def save_meta_infos_to_file(meta_infos, meta_info_path):
    # Convert timestamps to readable dates before saving
    for meta_info in meta_infos:
        if meta_info['oldest_post_date'] is not None and isinstance(meta_info['oldest_post_date'], int):
            meta_info['oldest_post_date'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                          time.localtime(meta_info['oldest_post_date']))
        if meta_info['newest_post_date'] is not None and isinstance(meta_info['newest_post_date'], int):
            meta_info['newest_post_date'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                          time.localtime(meta_info['newest_post_date']))
    with open(meta_info_path, 'w', encoding='utf-8') as f:
        json.dump(meta_infos, f, ensure_ascii=False, indent=4)


class VKApiRateLimiter:
    def __init__(self, max_calls_per_second):
        self.max_calls = max_calls_per_second
        self.lock = asyncio.Lock()
        self.calls = []

    async def wait(self):
        async with self.lock:
            now = time.monotonic()
            while self.calls and self.calls[0] <= now - 1:
                self.calls.pop(0)
            if len(self.calls) >= self.max_calls:
                sleep_time = 1 - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.calls.pop(0)
            self.calls.append(time.monotonic())


async def download_image(session, url, path):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.read()
            with open(path, 'wb') as f:
                f.write(content)
        return True
    except Exception as e:
        logger.error(f'Failed to download image {url}: {e}')
        return False


async def process_post(session, post, group_id_num, index_file_path, meta_info):
    # Count the number of photo attachments
    photo_attachments = [att for att in post.get('attachments', []) if att['type'] == 'photo']
    if len(photo_attachments) < 2:
        # Skip posts with less than 2 photos
        return
    images = []
    image_num = 1  # Initialize image number for this post
    download_tasks = []
    for attachment in photo_attachments:
        biggest_image = extract_image(attachment['photo'])
        if biggest_image is None or 'url' not in biggest_image:
            logger.warning(f'Cannot extract image from post: {post["id"]}')
            continue
        # Prepare the filename
        filename = f'vkg{group_id_num}_{post["id"]}_{image_num}.jpg'
        biggest_image['local_filename'] = filename
        path = os.path.join(imgs_dir, filename)
        # Schedule the download task
        download_tasks.append((biggest_image, path))
        image_num += 1  # Increment image number

    # Limit concurrent image downloads
    semaphore = asyncio.Semaphore(max_concurrent_image_downloads)

    async def semaphore_download(biggest_image, path):
        async with semaphore:
            success = await download_image(session, biggest_image['url'], path)
            if success:
                return biggest_image
            else:
                return None

    # Start image downloads
    tasks = [semaphore_download(img, path) for img, path in download_tasks]
    results = await asyncio.gather(*tasks)
    for res in results:
        if res:
            images.append(res)
    # After processing all attachments, write the index record
    if images:
        index_rec = construct_index_record(post, images, group_id_num)
        # Write to index file in the root directory
        append_index_record_to_file(index_rec, index_file_path)
        # Update meta information
        post_id = post['id']
        post_date = post['date']
        if meta_info['oldest_post_id'] is None or post_id < meta_info['oldest_post_id']:
            meta_info['oldest_post_id'] = post_id
            meta_info['oldest_post_date'] = post_date
        if meta_info['newest_post_id'] is None or post_id > meta_info['newest_post_id']:
            meta_info['newest_post_id'] = post_id
            meta_info['newest_post_date'] = post_date
        # Update meta_infos and save to file
        # Remove existing meta_info for this group if it exists
        global meta_infos
        meta_infos = [mi for mi in meta_infos if mi['group_id'] != group_id_num]
        # Add updated meta_info
        meta_infos.append(meta_info.copy())
        # Save meta_infos to file
        save_meta_infos_to_file(meta_infos, meta_info_file_p)


async def main():
    scrape_params = get_latest_scrape_params_from_file(scrape_params_file_p, default_parameters)
    vk_rate_limiter = VKApiRateLimiter(vk_api_rate_limit)
    os.makedirs(imgs_dir, exist_ok=True)

    global meta_infos
    meta_infos = get_latest_metainfo_from_file(meta_info_file_p)

    async with aiohttp.ClientSession() as session:
        for group in groups_to_search:
            group_id_str = group.id
            group_id_num = group.id_num

            logger.info(f'Start processing group: {group.id}')

            # Initialize meta information for the group
            meta_info = {
                'group_id': group_id_num,
                'group_name': group.id,
                'oldest_post_id': None,
                'oldest_post_date': None,
                'newest_post_id': None,
                'newest_post_date': None,
            }

            offset = scrape_params.get(group_id_str, {}).get('last_scrapped_offset', 0)
            has_more_posts = True
            num_errors = 0
            posts_downloaded = 0  # Initialize the counter for posts downloaded

            default_request_params = {
                'access_token': service_token,
                'v': '5.131',
                'owner_id': -group_id_num,  # owner_id is negative for groups
                'count': batch_size,
            }

            # First, get total number of posts
            try:
                await vk_rate_limiter.wait()
                count_request_params = default_request_params.copy()
                count_request_params['count'] = 1  # We only need one item to get the total count
                async with session.get(
                        'https://api.vk.com/method/wall.get',
                        params=count_request_params
                ) as response:
                    response_json = await response.json()
                    if 'error' in response_json:
                        logger.error(f"API Error: {response_json['error']}")
                        total_posts = None
                    elif 'response' in response_json and 'count' in response_json['response']:
                        total_posts = response_json['response']['count']
                        logger.info(f"Total posts to process: {total_posts} (limited to {max_posts_per_group})")
                    else:
                        logger.error('Unable to retrieve total post count for group: {}'.format(group.id))
                        total_posts = None
            except Exception as e:
                logger.error(f'Exception occurred while getting total posts: {e}')
                total_posts = None
                raise e

            if total_posts is not None and offset >= total_posts:
                logger.info(f'All posts have been processed for group: {group.id}')
                continue

            if total_posts is not None:
                total_posts_to_process = min(total_posts - offset, max_posts_per_group)
            else:
                total_posts_to_process = max_posts_per_group  # Limit to max_posts_per_group if total_posts is unknown

            with tqdm(desc=f'Processing group {group.id}', total=total_posts_to_process) as pbar:
                while has_more_posts and posts_downloaded < max_posts_per_group:
                    request_params = {**default_request_params, 'offset': offset}
                    try:
                        await vk_rate_limiter.wait()
                        async with session.get(
                                'https://api.vk.com/method/wall.get',
                                params=request_params
                        ) as response:
                            response_json = await response.json()
                            if 'error' in response_json:
                                logger.error(f"API Error: {response_json['error']}")
                                num_errors += 1
                                if num_errors > 5:
                                    logger.error("Too many errors, exiting.")
                                    break
                                await asyncio.sleep(1)
                                continue
                            elif 'response' in response_json and 'items' in response_json['response']:
                                items = response_json['response']['items']
                                num_items = len(items)
                                if num_items == 0:
                                    has_more_posts = False
                                    logger.info("No more posts to process.")
                                    break
                                # Adjust if fetching more than needed
                                if posts_downloaded + num_items > max_posts_per_group:
                                    num_items = max_posts_per_group - posts_downloaded
                                    items = items[:num_items]
                                    has_more_posts = False  # Reached the limit
                                # Process posts
                                tasks = [process_post(session, post, group_id_num, index_file_path, meta_info)
                                         for post in items]
                                await asyncio.gather(*tasks)
                                pbar.update(num_items)
                                posts_downloaded += num_items
                                if num_items < batch_size:
                                    has_more_posts = False
                                offset += num_items
                                scrape_params[group_id_str] = {'last_scrapped_offset': offset}
                                save_latest_scrape_params_to_file(scrape_params, scrape_params_file_p)
                                if posts_downloaded >= max_posts_per_group:
                                    logger.info(
                                        f"Reached max posts limit ({max_posts_per_group}) for group: {group.id}")
                                    has_more_posts = False
                            else:
                                logger.error('No more posts or unexpected response.')
                                has_more_posts = False
                    except Exception as e:
                        logger.error(f'Exception occurred: {e}')
                        num_errors += 1
                        if num_errors > 5:
                            logger.error("Too many errors, exiting.")
                            break
                        await asyncio.sleep(1)
                        continue

            logger.info(f'DONE processing group: {group.id}')

    # After processing all groups, save the combined meta information one last time
    save_meta_infos_to_file(meta_infos, meta_info_file_p)


if __name__ == '__main__':
    asyncio.run(main())
