import os
import torch
import torchreid
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import shutil

model_path = '/Users/albert.bikeev/Projects/sobaken-id/re-identification/log/v0.3_vkg34900407plus/model/model.pth.tar-33'
num_classes = 621
query_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/predictions/clean_dom_lapkin_1-3/query'
gallery_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/predictions/clean_dom_lapkin_1-3/gallery'
predictions_dir = '/Users/albert.bikeev/Projects/sobaken-id/data/predictions/clean_dom_lapkin_1-3/modelv0.3_vkg34900407plus'

# Define InferenceDataset
class InferenceDataset(Dataset):
    def __init__(self, img_paths, transform=None):
        self.img_paths = img_paths
        self.transform = transform

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img_path = self.img_paths[idx]
        img = Image.open(img_path).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, img_path  # Return image and its path

# Function to extract features
def extract_features(model, loader, device):
    features = []
    img_paths = []
    with torch.no_grad():
        for imgs, paths in loader:
            imgs = imgs.to(device)
            outputs = model(imgs)
            features.append(outputs.cpu())
            img_paths.extend(paths)
    features = torch.cat(features, dim=0)
    return features, img_paths

# Function to get top N matches
def get_top_n(distmat, query_paths, gallery_paths, top_n=5):
    distmat = distmat.numpy()
    num_queries = distmat.shape[0]
    results = []
    for i in range(num_queries):
        distances = distmat[i]
        indices = np.argsort(distances)  # Sort distances in ascending order
        top_indices = indices[:top_n]
        top_gallery_paths = [gallery_paths[idx] for idx in top_indices]
        results.append({
            'query_img': query_paths[i],
            'top_matches': top_gallery_paths,
            'distances': distances[top_indices]
        })
    return results

# def num_classes():
#     from dom_lapkin import DomLapkin4
#     torchreid.data.register_image_dataset('animals_dataset', DomLapkin4)
#
#     # Create the data manager
#     datamanager = torchreid.data.ImageDataManager(
#         root='/Users/albert.bikeev/Projects/sobaken-id/data/clean',
#         sources='animals_dataset',
#         height=256,
#         width=128,
#         batch_size_train=32,
#         batch_size_test=100,
#         transforms=['random_flip', 'random_crop', 'random_erase'],
#         num_instances=4,
#         train_sampler='RandomIdentitySampler',
#     )
#     print("datamanager.num_train_pids")
#     print(datamanager.num_train_pids)
#     return datamanager.num_train_pids

if __name__ == '__main__':
    # Paths to the query and gallery directories
    Path(predictions_dir).mkdir(parents=True, exist_ok=True)

    # Ensure the reid directory exists
    if os.path.exists(predictions_dir):
        shutil.rmtree(predictions_dir)
    os.makedirs(predictions_dir, exist_ok=True)

    # Load the model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # Build the model architecture
    model = torchreid.models.build_model(
        name='osnet_x1_0',
        num_classes=num_classes,
        loss='triplet',
        pretrained=False
    )

    # Load the trained weights
    state_dict = torch.load(model_path, map_location=device)['state_dict']
    model.load_state_dict(state_dict)
    model = model.to(device)
    model.eval()

    # Define transformations
    transform = transforms.Compose([
        transforms.Resize((256, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet mean
                             std=[0.229, 0.224, 0.225]),  # ImageNet std
    ])

    # Get image paths
    query_img_paths = [os.path.join(query_dir, img) for img in os.listdir(query_dir) if img.endswith('.jpg')]
    gallery_img_paths = [os.path.join(gallery_dir, img) for img in os.listdir(gallery_dir) if img.endswith('.jpg')]

    # Create datasets and loaders
    query_dataset = InferenceDataset(query_img_paths, transform=transform)
    gallery_dataset = InferenceDataset(gallery_img_paths, transform=transform)

    query_loader = DataLoader(query_dataset, batch_size=32, shuffle=False, num_workers=4)
    gallery_loader = DataLoader(gallery_dataset, batch_size=32, shuffle=False, num_workers=4)

    # Extract features
    print("Extracting features from query images...")
    query_features, query_paths = extract_features(model, query_loader, device)
    print("Extracting features from gallery images...")
    gallery_features, gallery_paths = extract_features(model, gallery_loader, device)

    # Compute distance matrix
    print("Computing distance matrix...")
    distmat = torchreid.metrics.compute_distance_matrix(query_features, gallery_features, metric='cosine')

    # Retrieve top 5 matches
    top_n = 5
    results = get_top_n(distmat, query_paths, gallery_paths, top_n=top_n)

    # Process results and save images
    print("Saving re-identification results...")
    for result in results:
        query_img_path = result['query_img']
        top_matches = result['top_matches']
        distances = result['distances']

        # Extract post-id and img-num from the query image filename
        query_filename = os.path.basename(query_img_path)
        query_basename, _ = os.path.splitext(query_filename)
        # Assuming the filename format is 'post-id_img-num.jpg'
        # Handle cases where the filename might have additional underscores
        split_name = query_basename.split('_')
        if len(split_name) >= 2:
            pid = split_name[0]
            img_num = split_name[1]
        else:
            print(f"Filename {query_filename} does not match expected format. Skipping.")
            continue

        # Save the query image with name 'post-id_img-num__query.jpg'
        new_query_filename = f"{pid}_{img_num}__query.jpg"
        new_query_path = os.path.join(predictions_dir, new_query_filename)
        shutil.copyfile(query_img_path, new_query_path)

        # Save the top 5 gallery images
        for idx, gallery_img_path in enumerate(top_matches):
            gallery_filename = os.path.basename(gallery_img_path)
            # Optionally, extract gallery image's post-id and img-num
            new_gallery_filename = f"{pid}_{img_num}_found{idx+1}.jpg"
            new_gallery_path = os.path.join(predictions_dir, new_gallery_filename)
            shutil.copyfile(gallery_img_path, new_gallery_path)

    print("Re-identification results saved in:", predictions_dir)
