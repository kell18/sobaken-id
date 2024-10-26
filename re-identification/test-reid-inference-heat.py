import os
import torch
import torchreid
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import shutil
from tqdm import tqdm
import cv2

# Import Grad-CAM
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image, preprocess_image


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


def get_top_n(distmat, query_paths, gallery_paths, top_n=5):
    num_queries = distmat.shape[0]
    results = []
    for i in range(num_queries):
        distances = distmat[i]
        indices = np.argsort(distances)  # Ascending order
        top_indices = indices[:top_n]
        top_gallery_paths = [gallery_paths[idx] for idx in top_indices]
        results.append({
            'query_img': query_paths[i],
            'top_matches': top_gallery_paths,
            'distances': distances[top_indices]
        })
    return results


def insert_suffix_before_identifier(filename, suffix='-heat'):
    base, ext = os.path.splitext(filename)

    if '__query' in base:
        parts = base.split('__query')
        new_base = f"{parts[0]}{suffix}__query"
    elif '_found' in base:
        idx = base.find('_found')
        new_base = f"{base[:idx]}{suffix}{base[idx:]}"
    else:
        # Handle unexpected filename format
        new_base = f"{base}{suffix}"
    return f"{new_base}{ext}"


def generate_and_save_activation_map(model, img_path, output_path, device, suffix='_heat', colormap='jet', alpha=0.4):
    """
    Generates an activation map for the given image using feature maps from the last conv layer

    Parameters:
    - model: Trained re-identification model.
    - img_path: Path to the original image.
    - output_path: Out path for the image with activation heatmap.
    - device: Device to run the model on ('cpu' or 'cuda').
    - suffix: Suffix to append before the identifier (e.g., '_heat').
    - colormap: Colormap to use for the activation map.
    - alpha: Blending factor for the activation map overlay.
    """
    try:
        # Load and preprocess image
        img = Image.open(img_path).convert('RGB')
        transform = transforms.Compose([
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])
        img_tensor = transform(img).unsqueeze(0).to(device)

        # Forward pass to get the feature maps
        with torch.no_grad():
            # Obtain the feature maps from the last convolutional layer
            # Modify the model to return the feature maps
            def hook_function(module, input, output):
                # Save the output in a variable accessible outside the hook
                global feature_maps
                feature_maps = output.detach()

            # Register hook to the last convolutional layer
            handle = model.conv5.register_forward_hook(hook_function)

            # Forward pass
            _ = model(img_tensor)

            # Remove the hook
            handle.remove()

            # feature_maps now contains the output from model.conv5
            # feature_maps shape: [batch_size, channels, height, width]
            activation = feature_maps[0]  # Take the first (and only) item in the batch

            # Compute the activation map as the sum of absolute values along the channel dimension
            activation_map = torch.sum(torch.abs(activation), dim=0)

            # Convert to numpy array
            activation_map = activation_map.cpu().numpy()

            # Apply spatial L2 normalization
            norm = np.linalg.norm(activation_map, ord=2)
            if norm != 0:
                activation_map = activation_map / norm

            # Normalize activation map to [0,1]
            activation_map = (activation_map - activation_map.min()) / (
                        activation_map.max() - activation_map.min() + 1e-8)

            # Resize activation map to match the input image size
            activation_map_resized = cv2.resize(activation_map, (128, 256))

            # Prepare image for visualization
            img_resized = img.resize((128, 256))
            img_np = np.array(img_resized).astype(np.float32) / 255.0  # Normalize to [0,1]
            img_np = img_np[..., :3]  # Ensure 3 channels

            # Choose a colormap
            import matplotlib.pyplot as plt
            cmap = plt.get_cmap(colormap)
            heatmap = cmap(activation_map_resized)[:, :, :3]  # Remove alpha channel

            # Superimpose heatmap on the image
            visualization = heatmap * alpha + img_np * (1 - alpha)

            # Clip values to [0,1]
            visualization = np.clip(visualization, 0, 1)

            # Save the activation map
            heatmap_filename = insert_suffix_before_identifier(os.path.basename(output_path), suffix=suffix)
            heatmap_path = os.path.join(os.path.dirname(output_path), heatmap_filename)

            # Convert RGB to BGR for OpenCV
            visualization_bgr = cv2.cvtColor((visualization * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
            cv2.imwrite(heatmap_path, visualization_bgr)

    except Exception as e:
        print(f"Error generating activation map for {img_path}: {e}")


def main():
    base_dataset_path = '/Users/albert.bikeev/Projects/sobaken-id/data/predictions/clean_dom_lapkin_4'
    base_model_path = '/Users/albert.bikeev/Projects/sobaken-id/re-identification/log/v0.1.60e-dl1-3'
    num_classes = 235  # Adjust to your number of classes
    model_paths_to_names = {
        f'{base_model_path}/model/model.pth.tar-3': 'modelv0.1.03e-dl1-3_top5-heat',
        f'{base_model_path}/model/model.pth.tar-12': 'modelv0.1.12e-dl1-3_top5-heat',
        f'{base_model_path}/model/model.pth.tar-30': 'modelv0.1.30e-dl1-3_top5-heat',
        f'{base_model_path}/model/model.pth.tar-60': 'modelv0.1.60e-dl1-3_top5-heat'
    }
    for model_path, model_name in model_paths_to_names.items():
        print(f'Generating activation maps for {model_name}...')

        query_dir = f'{base_dataset_path}/query'
        gallery_dir = f'{base_dataset_path}/gallery'
        predictions_dir = f'{base_dataset_path}/{model_name}'

        # Ensure the predictions directory exists
        if os.path.exists(predictions_dir):
            shutil.rmtree(predictions_dir)
        os.makedirs(predictions_dir, exist_ok=True)

        # Build the model architecture
        model = torchreid.models.build_model(
            name='osnet_x1_0',
            num_classes=num_classes,  # Should match your training
            loss='softmax',
            pretrained=False
        )

        # Load the trained weights
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        state_dict = torch.load(model_path, map_location=device)['state_dict']
        model.load_state_dict(state_dict)
        model = model.to(device)
        model.eval()

        # Get image paths
        query_img_paths = [os.path.join(query_dir, img) for img in os.listdir(query_dir) if
                           img.lower().endswith(('.jpg', '.png', '.jpeg'))]
        gallery_img_paths = [os.path.join(gallery_dir, img) for img in os.listdir(gallery_dir) if
                             img.lower().endswith(('.jpg', '.png', '.jpeg'))]

        # Define transformations
        transform = transforms.Compose([
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet mean
                                 std=[0.229, 0.224, 0.225]),  # ImageNet std
        ])

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
        distmat = torchreid.metrics.compute_distance_matrix(query_features, gallery_features, metric='euclidean')
        distmat = distmat.numpy()

        # Retrieve top 5 matches
        top_n = 5
        results = get_top_n(distmat, query_paths, gallery_paths, top_n=top_n)

        # Process results and save images
        print("Saving re-identification results and generating attention maps...")
        for result in tqdm(results, desc="Processing query images"):
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

            # Generate attention map for the query image
            generate_and_save_activation_map(model, query_img_path, new_query_path, device, suffix='_heat')

            # Save the top 5 gallery images
            for idx, gallery_img_path in enumerate(top_matches):
                gallery_filename = os.path.basename(gallery_img_path)
                # Optionally, extract gallery image's post-id and img-num
                new_gallery_filename = f"{pid}_{img_num}_found{idx + 1}.jpg"
                new_gallery_path = os.path.join(predictions_dir, new_gallery_filename)
                shutil.copyfile(gallery_img_path, new_gallery_path)

                # Generate attention map for the gallery image
                generate_and_save_activation_map(model, gallery_img_path, new_gallery_path, device, suffix='_heat')

        print("Re-identification results and attention maps saved in:", predictions_dir)


if __name__ == '__main__':
    main()
