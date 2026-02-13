import torch.nn as nn
from torchvision.models import resnet18


def build_model(num_classes: int = 10) -> nn.Module:
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model
