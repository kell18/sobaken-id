import glob
import os
from torchreid.data.datasets import ImageDataset

def extract_pid(filename):
    """
    Extracts the person ID (pid) from the filename based on the new format:
    'vkg<GROUP_ID>_<POST_ID>_<IMAGE_NUM>.jpg'

    Args:
        filename (str): The image filename.

    Returns:
        str: The combined pid as '<GROUP_ID>_<POST_ID>'.
    """
    basename, _ = os.path.splitext(filename)
    if basename.startswith('vkg'):
        basename = basename[3:]  # Remove 'vkg' prefix
    parts = basename.split('_')
    if len(parts) >= 3:
        group_id = parts[0]
        post_id = parts[1]
        pid = f"{group_id}_{post_id}"
        return pid
    else:
        print(f"Filename '{filename}' does not match the expected format.")
        return None

def collect_pids(dir_path, pathPattern='*.jpg'):
    """
    Collects all unique person IDs from the specified directory.

    Args:
        dir_path (str): The directory path.
        pathPattern (str): The pattern to match filenames.

    Returns:
        set: A set of unique pids.
    """
    img_paths = glob.glob(os.path.join(dir_path, pathPattern))
    pid_set = set()
    for img_path in img_paths:
        filename = os.path.basename(img_path)
        pid = extract_pid(filename)
        if pid is not None:
            pid_set.add(pid)
    return pid_set

def process_dir(dir_path, relabel=False, pathPattern='*.jpg', pid2label=None):
    """
    Processes the directory to prepare the dataset.

    Args:
        dir_path (str): Directory path.
        relabel (bool): Whether to relabel pids to have consecutive labels.
        pathPattern (str): Glob pattern to match image files.
        pid2label (dict): Mapping from pid to label (used when relabel=False).

    Returns:
        list: A list of tuples (img_path, pid_label, camid).
    """
    img_paths = glob.glob(os.path.join(dir_path, pathPattern))
    data = []
    pid_container = set()

    if relabel:
        # For training set, build pid2label mapping
        for img_path in img_paths:
            filename = os.path.basename(img_path)
            pid = extract_pid(filename)
            if pid is None:
                continue
            pid_container.add(pid)
        pid2label = {pid: label for label, pid in enumerate(sorted(pid_container))}
    else:
        # For query/gallery, pid2label must be provided
        assert pid2label is not None, "pid2label mapping must be provided for relabel=False"

    for img_path in img_paths:
        filename = os.path.basename(img_path)
        pid = extract_pid(filename)
        if pid is None:
            continue
        pid_label = pid2label[pid]
        if relabel:
            camid = 0  # Assuming single camera for training images
        else:
            dirname = os.path.basename(dir_path)
            if dirname == 'query':
                camid = 0  # Assign camid = 0 to query images
            elif dirname == 'gallery':
                camid = 1  # Assign camid = 1 to gallery images
            else:
                camid = 0  # Default camera ID
        data.append((img_path, pid_label, camid))
    return data

class DomLapkin4(ImageDataset):
    dataset_dir = 'clean_dom_lapkin_4'

    def __init__(self, root='', **kwargs):
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.train_dir = os.path.join(self.dataset_dir, 'train')
        self.query_dir = os.path.join(self.dataset_dir, 'query')
        self.gallery_dir = os.path.join(self.dataset_dir, 'gallery')

        self.check_before_run([self.train_dir, self.query_dir, self.gallery_dir])

        # Process the training set
        train = process_dir(self.train_dir, relabel=True, pathPattern='*/*.jpg')

        # Collect pids from query and gallery
        query_pids = collect_pids(self.query_dir)
        gallery_pids = collect_pids(self.gallery_dir)
        all_pids = query_pids.union(gallery_pids)
        pid2label_qg = {pid: label for label, pid in enumerate(sorted(all_pids))}

        # Process the query and gallery sets
        query = process_dir(self.query_dir, relabel=False, pid2label=pid2label_qg)
        gallery = process_dir(self.gallery_dir, relabel=False, pid2label=pid2label_qg)

        super(DomLapkin4, self).__init__(train, query, gallery, **kwargs)

class DomLapkin13(ImageDataset):
    dataset_dir = 'clean_dom_lapkin_1-3'

    def __init__(self, root='', **kwargs):
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.train_dir = os.path.join(self.dataset_dir, 'train')
        self.query_dir = os.path.join(self.dataset_dir, 'query')
        self.gallery_dir = os.path.join(self.dataset_dir, 'gallery')

        self.check_before_run([self.train_dir, self.query_dir, self.gallery_dir])

        # Process the training set
        train = process_dir(self.train_dir, relabel=True, pathPattern='*/*.jpg')

        # Collect pids from query and gallery
        query_pids = collect_pids(self.query_dir)
        gallery_pids = collect_pids(self.gallery_dir)
        all_pids = query_pids.union(gallery_pids)
        pid2label_qg = {pid: label for label, pid in enumerate(sorted(all_pids))}

        # Process the query and gallery sets
        query = process_dir(self.query_dir, relabel=False, pid2label=pid2label_qg)
        gallery = process_dir(self.gallery_dir, relabel=False, pid2label=pid2label_qg)

        super(DomLapkin13, self).__init__(train, query, gallery, **kwargs)

class DomLapkin2(ImageDataset):
    dataset_dir = 'clean_dom_lapkin_2'

    def __init__(self, root='', **kwargs):
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.train_dir = os.path.join(self.dataset_dir, 'train')
        self.query_dir = os.path.join(self.dataset_dir, 'query')
        self.gallery_dir = os.path.join(self.dataset_dir, 'gallery')

        self.check_before_run([self.train_dir, self.query_dir, self.gallery_dir])

        # Process the training set
        train = process_dir(self.train_dir, relabel=True, pathPattern='*/*.jpg')

        # Collect pids from query and gallery
        query_pids = collect_pids(self.query_dir)
        gallery_pids = collect_pids(self.gallery_dir)
        all_pids = query_pids.union(gallery_pids)
        pid2label_qg = {pid: label for label, pid in enumerate(sorted(all_pids))}

        # Process the query and gallery sets
        query = process_dir(self.query_dir, relabel=False, pid2label=pid2label_qg)
        gallery = process_dir(self.gallery_dir, relabel=False, pid2label=pid2label_qg)

        super(DomLapkin2, self).__init__(train, query, gallery, **kwargs)
