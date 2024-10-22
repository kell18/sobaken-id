import torchreid
from torchreid.utils import FeatureExtractor

# TODO
# Prepare some data using ChatGPT response
# Create Dataset class here

# Initialize the feature extractor
extractor = FeatureExtractor(
    model_name='resnet50',
    model_path='log/resnet50/model.pth.tar',  # Path to your trained model
    device='cuda'  # or 'cpu'
)
embeddings = extractor(['path/to/image1.jpg', 'path/to/image2.jpg'])

datamanager = torchreid.data.ImageDataManager(
    root="reid-data",
    sources="market1501",
    targets="market1501",
    height=256, width=128,
    batch_size_train=32,
    batch_size_test=100,
    transforms=["random_flip", "random_crop"]
)

model = torchreid.models.build_model(
    name="resnet50",
    num_classes=datamanager.num_train_pids,
    loss="softmax",
    pretrained=True
)

optimizer = torchreid.optim.build_optimizer(
    model,
    optim="adam",
    lr=0.0003
)

scheduler = torchreid.optim.build_lr_scheduler(
    optimizer,
    lr_scheduler="single_step",
    stepsize=20
)

engine = torchreid.engine.ImageSoftmaxEngine(
    datamanager,
    model,
    optimizer=optimizer,
    scheduler=scheduler,
    label_smooth=True
)

engine.run(
    save_dir="log/resnet50",
    max_epoch=60,
    eval_freq=10,
    print_freq=10,
    test_only=False
)
