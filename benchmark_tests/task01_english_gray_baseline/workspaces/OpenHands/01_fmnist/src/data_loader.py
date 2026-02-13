from torchvision import datasets, transforms
from torch.utils.data import DataLoader


def get_fashion_mnist_loaders(batch_size: int = 64):
    transform = transforms.Compose(
        [
            transforms.RandomRotation(degrees=15),
            transforms.RandomAffine(degrees=0, scale=(0.9, 1.1)),
            transforms.ToTensor(),
        ]
    )

    train_dataset = datasets.FashionMNIST(
        root="data",
        train=True,
        download=True,
        transform=transform,
    )
    test_dataset = datasets.FashionMNIST(
        root="data",
        train=False,
        download=True,
        transform=transforms.ToTensor(),
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    return train_loader, test_loader
