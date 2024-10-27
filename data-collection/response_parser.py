import json
import urllib.request


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
