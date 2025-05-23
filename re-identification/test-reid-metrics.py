import torch
import torchreid
from my_datasets.dom_lapkin import DomLapkin13
import glob
import os
from torchreid.data.datasets import ImageDataset

results_save_dir = 'log/test_dom_lapkin2_osnet'
model_path = '/Users/albert.bikeev/Projects/sobaken-id/re-identification/log/v0.1.60e-dl1-3/model/model.pth.tar-30'

if __name__ == '__main__':

    torchreid.data.register_image_dataset('animals_dataset', DomLapkin13)

    # Create the data manager
    datamanager = torchreid.data.ImageDataManager(
        root='/Users/albert.bikeev/Projects/sobaken-id/data/clean',
        sources='animals_dataset',
        height=256,
        width=128,
        batch_size_train=32,
        batch_size_test=100,
        transforms=['random_flip', 'random_crop', 'random_erase'],
        num_instances=4,
        train_sampler='RandomIdentitySampler',
    )

    # Load the model architecture
    model = torchreid.models.build_model(
        name='osnet_x1_0',
        num_classes=datamanager.num_train_pids,  # Replace with the number of classes used during training
        loss='triplet',
        pretrained=False
    )

    # Load the trained weights
    print(f"Evaluating model {model_path}...")
    state_dict = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state_dict['state_dict'])

    # Move the model to GPU if available
    model = model.cuda() if torch.cuda.is_available() else model

    # Set the model to evaluation mode
    model.eval()

    from PIL import Image
    from torchvision import transforms

    # Define the transformations (should match those used during training)
    transform_test = torchreid.data.transforms.build_transforms(
        height=256,
        width=128,
        transforms=None,  # No data augmentation during testing
        norm_mean=[0.485, 0.456, 0.406],
        norm_std=[0.229, 0.224, 0.225],
    )

    def preprocess_image(img_path):
        img = Image.open(img_path).convert('RGB')
        img = transform_test(img)
        img = img.unsqueeze(0)  # Add batch dimension
        return img


    # Build engine
    engine = torchreid.engine.ImageTripletEngine(
        datamanager,
        model,
        optimizer=None,
        scheduler=None
    )

    # Run training
    engine.run(
        test_only=True,
        save_dir=results_save_dir,
        max_epoch=0,
    )
