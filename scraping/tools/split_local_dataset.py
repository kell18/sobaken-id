import json
import shutil

orig_imgs_base_p = '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded/dom_lapkin/imgs/'

to_split = {
    # '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded/dom_lapkin_split/dom_lapkin_1/': 'index_dom_lapkin_1.json',
    '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded/dom_lapkin_split/dom_lapkin_2/': 'index_dom_lapkin_2.json',
    '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded/dom_lapkin_split/dom_lapkin_3/': 'index_dom_lapkin_3.json',
    '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded/dom_lapkin_split/dom_lapkin_4/': 'index_dom_lapkin_4.json',
    '/Users/albert.bikeev/Disk/nko/sobaken-id/scraping/resources/downloaded/dom_lapkin_split/dom_lapkin_5/': 'index_dom_lapkin_5.json'
}

# Костыль чтобы разбить большие датасеты на файлы поменьше чтобы влезло в Я. Диск
# TODO допилить scraping чтобы на уже скачивал небольшими кусками
if __name__ == '__main__':
    for (targ_base_path, targ_index) in to_split.items():
        with open(targ_base_path + targ_index) as targ_index_f:
            for index_line in targ_index_f:
                file_name = json.loads(index_line)['photo']['local_filename']

                shutil.copy(orig_imgs_base_p + file_name, targ_base_path + 'imgs/' + file_name)
