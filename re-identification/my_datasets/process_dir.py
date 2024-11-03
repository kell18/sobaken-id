import glob
import os

def process_dir(dir_path, relabel=False, pathPattern='*.jpg'):
    img_paths = glob.glob(os.path.join(dir_path, pathPattern))
    query_pids = set()
    gallery_pids = set()

    pid_container = set()
    if relabel:
        # Process training set
        for img_path in img_paths:
            filename = os.path.basename(img_path)
            group_id, post_id, img_num = filename.split('_')
            pid = group_id[:3] + '_' + post_id
            pid_container.add(pid)
        pid2label = {pid: label for label, pid in enumerate(sorted(pid_container))}
        data = []
        for img_path in img_paths:
            filename = os.path.basename(img_path)
            group_id, post_id, img_num = filename.split('_')
            pid = group_id[:3] + '_' + post_id
            pid_label = pid2label[pid]
            camid = 0  # Assuming single camera for training images
            data.append((img_path, pid_label, camid))
    else:
        # Process query and gallery sets
        data = []
        for img_path in img_paths:
            filename = os.path.basename(img_path)
            group_id, post_id, img_num = filename.split('_')
            pid = group_id[:3] + '_' + post_id
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
