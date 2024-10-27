import json
import urllib.request
import traceback
import requests
import time
import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class VKGroup:
    id: str
    id_num: int
    city: str | None # in Russian, None for non-city specific groups
    country2letters: str = 'ru'


service_token = os.environ['VK_SERVICE_TOKEN']

groups_to_search = [
    VKGroup('poisk_ul', 34900407, 'Ульяновск'),
    VKGroup('poteryha', 29426442, 'Барнаул'),
    VKGroup('poteryashki_karelia', 83381493, 'Карелия'),
    VKGroup('club81472745', 81472745, 'Казань'),
    VKGroup('myhomeforpet', 133848717, 'Альметьевск'),
    VKGroup('club30323533', 30323533, 'Краснодар'),
    VKGroup('sledopit.online', 198498843, None),
    VKGroup('goodhandshelp', 42062020, None),
    VKGroup('poisk_zhivotnykh', 205909292, None),
    # '-85905684': 'zoovestyekat',  # https://vk.com/zoovestyekat
    # '-83381493': 'poteryashki_karelia',  # https://vk.com/poteryashki_karelia
    # '-187961884': 'dom_lapkin',  # https://vk.com/dom_lapkin
]

imgs_upload_dir_w_trail_slash = '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded/'
scrape_params_file_full_path = '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/parameters.json'

white_list_kws = (
    'собака', 'кошка', 'кот', 'кутята', 'пёс', 'пес', 'пёсель', 'песель', 'собакен',
    'животное', 'кличка', 'потерялось', 'потярелос', 'потирялось', 'нашл', 'найд',
    'пропал', 'вознаграждение', 'убежал', 'бежал', 'украли', 'поймали', 'ошейник', 'ощейник',
    'отзовись', 'хозяин', 'бросили', 'собаку', 'нашли', 'потеряли', 'потерялся', 'убежал', 'убежала', 'кошку', 'пса',
    'намордник', 'связи', 'заголовок', 'пёселя', 'песеля', 'кош',
    'попуг', 'попуг', 'черепах', 'черепаш', 'животинка', 'найт', 'прибилась', 'прибился', 'брошен',
    'порода', 'кабель', 'кобель', 'сука', 'самка', 'самец'
)
posts_hashes_to_ignore = ['lWKtHAgxvI63OoD8fw']

sleep_sec_between_requests = 0.7
batch_size = 100  # num posts in each request to fetch (max = 100)
num_iterations = 7

default_parameters = {"last_scrapped_offset": 0, "last_error": None}

def extract_image(attachment_photo):
    if 'orig_photo' in attachment_photo:
        return attachment_photo['orig_photo']
    elif 'sizes' in attachment_photo and len(attachment_photo['sizes']) > 0:
        biggest_height_img = sorted(attachment_photo['sizes'], key=lambda a: a['height'], reverse=True)[0]
        return biggest_height_img
    else:
        return None


def construct_index_record(item, biggest_images):
    return {
        "post_id": item['id'],
        "text": item['text'],
        "photo": biggest_images,
        "full_link": get_post_full_link(item['owner_id'], item['id']),
        "date_ts": item['date'],
        "from_id": item['from_id'],
    }


def append_index_record_to_file(index_record, full_file_path):
    with open(full_file_path, "a") as myfile:
        record_str = json.dumps(index_record, ensure_ascii=False)
        myfile.write(record_str + '\n')


def get_post_full_link(the_owner_id, post_id):
    return f'https://vk.com/wall{the_owner_id}_{post_id}'


def string_contains_any_from_list(string, any_to_contain):
    return any(to_contain in string for to_contain in any_to_contain)

attachment_types_to_skip = ['doc', 'video', 'link', 'audio']

def download_image_and_update_index(post_hashes_to_ignore, imgs_upload_path_w_trail_slash, index_file_full_path,
                                    vk_response, white_list_kws):
    for post in vk_response['items']:
        if post['hash'] in post_hashes_to_ignore:
            print(f'Skipping ignored post with hash {post["hash"]}')
            continue
        if not string_contains_any_from_list(post['text'].lower(), white_list_kws):
            print(f'Skipping post without any required kw in: {post["text"]}')

        for attachment in post['attachments']:
            if attachment['type'] == 'photo':
                biggest_image = extract_image(attachment['photo'])
                if biggest_image is None or 'url' not in biggest_image:
                    raise Exception(
                        'Cannot extract biggest image from post: ' + json.dumps(post, ensure_ascii=False))
                # Download the photo:
                filename = biggest_image['url'].split('/')[-1].split('?')[0]
                biggest_image['local_filename'] = filename
                path = imgs_upload_path_w_trail_slash + filename
                urllib.request.urlretrieve(biggest_image['url'], path)
                # Update index file:
                index_rec = construct_index_record(post, biggest_image)
                append_index_record_to_file(index_rec, index_file_full_path)
            elif attachment['type'] in attachment_types_to_skip:
                print(f'Skipping link/video attachment with for post hash {post["hash"]}')
            else:
                raise Exception(
                    f'Skipping unknown attachment type {attachment["type"]}: {json.dumps(attachment, ensure_ascii=False)}')


def get_latest_scrape_params_from_file(scrape_params_file_path):
    file_params = None
    with open(scrape_params_file_path, 'r') as f:
        file_params = json.load(f)
    if file_params is not None:
        return file_params
    else:
        return default_parameters


def save_latest_scrape_params_to_file(scrape_params, scrape_params_file_path):
    with open(scrape_params_file_path, 'w') as f:
        json.dump(scrape_params, f)


if __name__ == '__main__':
    scrape_params = get_latest_scrape_params_from_file(scrape_params_file_full_path)
    num_errors = 0
    offset = scrape_params['last_scrapped_offset']
    for group in groups_to_search:
        imgs_upload_path_w_trail_slash = imgs_upload_dir_w_trail_slash + 'imgs_' + group.id + '/'
        index_file_full_path = imgs_upload_dir_w_trail_slash + 'index_' + group.id + '.json'

        print(f'Start processing group: {group.id} in {num_iterations} iterations, imgs '
              f'path: {imgs_upload_path_w_trail_slash}, index path: {index_file_full_path}')

        default_request_params = {
            'access_token': service_token,
            'v': '5.199',
            'owner_id': group.id,
            'count': batch_size,
        }

        for iteration in range(num_iterations):
            startT = time.time()
            print(f'Iteration #{iteration} / {num_iterations} with offset {offset}')
            request_params = {**default_request_params, 'offset': offset}
            if num_errors > 5:
                raise Exception('Too many errors, check logs')

            try:
                response = requests.get(
                    f'https://api.vk.com/method/wall.get',
                    params=request_params
                )
                response.raise_for_status()
                response_json = response.json()
                if 'response' in response_json and 'items' in response_json['response']:
                    Path(imgs_upload_path_w_trail_slash).mkdir(parents=True, exist_ok=True)
                    download_image_and_update_index(posts_hashes_to_ignore, imgs_upload_path_w_trail_slash,
                                                    index_file_full_path, response_json['response'], white_list_kws)
                else:
                    raise Exception('Unknown VK response: ' + str(response_json))

            except Exception as e:
                print('Exception occurred: ', traceback.format_exc())
                num_errors += 1

            new_scrape_params = {**scrape_params, 'last_scrapped_offset': offset + batch_size}
            save_latest_scrape_params_to_file(new_scrape_params, scrape_params_file_full_path)

            print(f'DONE Iteration #{iteration} / {num_iterations} in {time.time() - startT} sec')
            time.sleep(sleep_sec_between_requests)
            offset += batch_size
        offset = 0
        print(f'DONE processing group_id: {group.id}')
