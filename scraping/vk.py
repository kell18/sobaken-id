import json
import traceback
import requests
import time
import os
from scraping.response_parser import download_image_and_update_index

service_token = os.environ['VK_SERVICE_TOKEN']
owner_id = '-92601599'  # 'agatalifenews'

imgs_upload_path_w_trail_slash = '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded_imgs/'
index_file_full_path = '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/index_with_some_duplicates.json'
scrape_params_file_full_path = '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/parameters.json'

posts_hashes_to_ignore = ['lWKtHAgxvI63OoD8fw']

sleep_sec_between_requests = 0.7
batch_size = 100  # num posts in each request to fetch (max = 100)
num_iterations = 30

default_parameters = {"last_scrapped_offset": 0, "last_error": None}


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


# Next steps:
# + Отдельно обработать сценарий где type=link
# + выкачивать самое высокое качество
# + сохранять все параметры запроса в лок. файл чтобы можно было просто перезапускать откуда остановлися
# + вытянуть фотки в одну папку, но с индексным файлом

if __name__ == '__main__':
    scrape_params = get_latest_scrape_params_from_file(scrape_params_file_full_path)
    num_errors = 0
    default_request_params = {
        'access_token': service_token,
        'v': '5.199',
        'owner_id': owner_id,
        'count': batch_size,
    }
    offset = scrape_params['last_scrapped_offset']
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
                download_image_and_update_index(posts_hashes_to_ignore, imgs_upload_path_w_trail_slash,
                                                index_file_full_path, response_json['response'])
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
