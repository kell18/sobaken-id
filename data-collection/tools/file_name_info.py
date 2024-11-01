import os
from dataclasses import dataclass

@dataclass
class FileNameInfo:
    group_id: str
    post_id: str
    unique_post_id: str
    image_num: int
    file_name: str
    full_path: str

    @staticmethod
    def from_full_path(full_path):
        file_name = os.path.basename(full_path)
        name, ext = os.path.splitext(file_name)
        parts = name.split('_')
        if len(parts) != 3:
            raise ValueError(f'Invalid file name: {file_name}, expected vkg<GROUP_ID>_<POST_ID>_<IMG_NUM>.jpg format')
        group_id, post_id, image_num = parts
        group_id = group_id[3:]
        return FileNameInfo(group_id, post_id, group_id + '_' + post_id, image_num, file_name, full_path)
