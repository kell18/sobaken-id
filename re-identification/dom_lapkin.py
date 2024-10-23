import glob
import os
from torchreid.data.datasets import ImageDataset

def process_dir(dir_path, relabel=False, pathPattern='*.jpg'):
    img_paths = glob.glob(os.path.join(dir_path, pathPattern))
    query_pids = set()
    gallery_pids = set()

    pid_container = set()
    if relabel:
        # Process training set
        for img_path in img_paths:
            filename = os.path.basename(img_path)
            pid = filename.split('_')[0]
            pid_container.add(pid)
        pid2label = {pid: label for label, pid in enumerate(sorted(pid_container))}
        data = []
        for img_path in img_paths:
            filename = os.path.basename(img_path)
            pid = filename.split('_')[0]
            pid_label = pid2label[pid]
            camid = 0  # Assuming single camera for training images
            data.append((img_path, pid_label, camid))
    else:
        # Process query and gallery sets
        data = []
        for img_path in img_paths:
            filename = os.path.basename(img_path)
            pid = filename.split('_')[0]
            if not pid.isdigit():
                print(f"Invalid PID '{pid}' extracted from filename: {filename}")
                continue  # Skip or handle the error
            pid_int = int(pid)
            if os.path.basename(dir_path) == 'query':
                camid = 0  # Assign camid = 0 to query images
                query_pids.add(pid_int)
            elif os.path.basename(dir_path) == 'gallery':
                camid = 1  # Assign camid = 1 to gallery images
                gallery_pids.add(pid_int)
            else:
                camid = 0  # Default camera ID
            data.append((img_path, pid_int, camid))
    # Verify that all query PIDs are in the gallery
    # missing_pids = query_pids - gallery_pids
    # if missing_pids:
    #     raise ValueError(f"Identities {missing_pids} are present in query but missing in gallery.")
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

        # Process the query and gallery sets
        query = process_dir(self.query_dir, relabel=False)
        gallery = process_dir(self.gallery_dir, relabel=False)

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

        # Process the query and gallery sets
        query = process_dir(self.query_dir, relabel=False)
        gallery = process_dir(self.gallery_dir, relabel=False)

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

        # Process the query and gallery sets
        query = process_dir(self.query_dir, relabel=False)
        gallery = process_dir(self.gallery_dir, relabel=False)

        super(DomLapkin2, self).__init__(train, query, gallery, **kwargs)
