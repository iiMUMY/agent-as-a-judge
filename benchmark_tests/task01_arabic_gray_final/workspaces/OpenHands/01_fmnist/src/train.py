import os
import torch
from tqdm import tqdm


def train_one_epoch(model, train_loader, optimizer, criterion, device):
    model.train()
    for images, labels in tqdm(train_loader, desc="training", leave=False):
        images = images.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()


def save_model(model, base_dir: str = "."):
    save_dir = os.path.join(base_dir, "models", "saved_models")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "fashionnet.pt")
    torch.save(model.state_dict(), save_path)
    return save_path
