import torch
import torchreid
from torchreid.engine import ImageTripletEngine, ImageSoftmaxEngine
from my_datasets.vkg34900407plus import Vkg34900407plus
import wandb

training_model_version = '0.3_vkg34900407plus'

if __name__ == '__main__':
    run = wandb.init(project="sobaken-id", name=f'train_reid_v{training_model_version}',
                     settings=wandb.Settings(_disable_stats=True, _disable_meta=True))

    dataset = Vkg34900407plus
    save_dir = f'log/v{training_model_version}'

    config = run.config
    config.base_pretrained_model = 'osnet_x1_0'
    config.dataset_name = dataset.name

    config.transforms = ['random_flip', 'random_crop', 'random_erase']

    config.optimizer = 'adam'
    config.loss = 'triplet'
    config.learning_rate = 3e-4

    config.scheduler_method = 'single_step'
    config.scheduler_stepsize = 20

    config.max_epochs = 60

    print(f'train_model_version: {training_model_version}, configuration: {config}')

    torchreid.data.register_image_dataset(dataset.name, dataset)

    # Create the data manager
    datamanager = torchreid.data.ImageDataManager(
        root=dataset.base_path,
        sources=dataset.name,
        height=256,
        width=128,
        batch_size_train=32,
        batch_size_test=100,
        transforms=config.transforms,
        num_instances=4,
        train_sampler='RandomIdentitySampler',
    )

    print(f"Number of training identities: {datamanager.num_train_pids}")

    # Build the model
    model = torchreid.models.build_model(
        name=config.base_pretrained_model,
        num_classes=datamanager.num_train_pids,
        loss=config.loss,
        pretrained=True
    )

    # Move the model to GPU if available
    model = model.cuda() if torch.cuda.is_available() else model

    # Print model's classifier output dimension
    print(f"Model's classifier output dimension: {model.classifier.out_features}")

    # Build optimizer and scheduler
    optimizer = torchreid.optim.build_optimizer(
        model,
        optim=config.optimizer,
        lr=config.learning_rate,
    )
    scheduler = torchreid.optim.build_lr_scheduler(
        optimizer,
        lr_scheduler=config.scheduler_method,
        stepsize=config.scheduler_stepsize
    )

    engine_class = ImageTripletEngine if config.loss == 'triplet' else ImageSoftmaxEngine

    # Build engine
    engine = engine_class(
        datamanager,
        model,
        optimizer=optimizer,
        scheduler=scheduler,
        label_smooth=True,
        log_metrics=lambda metrics: run.log(metrics),
    )

    try:
        # Run training
        engine.run(
            save_dir=save_dir,
            max_epoch=config.max_epochs,
            eval_freq=3,
            print_freq=10,
            test_only=False
        )
    finally:
        print('Training was finished or interrupted, trying to send WanDB metrics...')
        run.finish()
        print('WanDB metrics are sent.')
