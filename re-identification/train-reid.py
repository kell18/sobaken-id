import torch
import torchreid
from dom_lapkin import DomLapkin13
import glob
import os
from torchreid.data.datasets import ImageDataset


if __name__ == '__main__':

    torchreid.data.register_image_dataset('DomLapkin13', DomLapkin13)

    # Create the data manager
    datamanager = torchreid.data.ImageDataManager(
        root='/Users/albert.bikeev/Projects/sobaken-id/data/clean',
        sources='DomLapkin13',
        height=256,
        width=128,
        batch_size_train=32,
        batch_size_test=100,
        transforms=['random_flip', 'random_crop', 'random_erase'],
        num_instances=4,
        train_sampler='RandomIdentitySampler',
    )

    # Build the model
    model = torchreid.models.build_model(
        name='osnet_x1_0',
        num_classes=datamanager.num_train_pids,
        loss='triplet',
        pretrained=True
    )
    # Move the model to GPU if available
    model = model.cuda() if torch.cuda.is_available() else model

    # Build optimizer and scheduler
    optimizer = torchreid.optim.build_optimizer(
        model,
        optim='adam',
        lr=3e-4
    )
    scheduler = torchreid.optim.build_lr_scheduler(
        optimizer,
        lr_scheduler='single_step',
        stepsize=20
    )

    # Build engine
    engine = torchreid.engine.ImageSoftmaxEngine(
        datamanager,
        model,
        optimizer=optimizer,
        scheduler=scheduler,
        label_smooth=True
    )

    # Run training
    engine.run(
        save_dir='log/v0.1.12e_lTrip-dl1-3',
        max_epoch=12,
        eval_freq=3,
        print_freq=3,
        test_only=False
    )
