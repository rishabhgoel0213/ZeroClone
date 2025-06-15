import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset
import numpy as np

import torch.nn as nn

class ResidualBlock(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.seq = nn.Sequential \
        (
            nn.Conv2d(c, c, 3, padding=1, bias=False),
            nn.BatchNorm2d(c),
            nn.ReLU(inplace=True),
            nn.Conv2d(c, c, 3, padding=1, bias=False),
            nn.BatchNorm2d(c),
        )
        self.relu = nn.ReLU(inplace=True)
    def forward(self, x):
        return self.relu(x + self.seq(x))

class ValueNetwork(nn.Module):
    def __init__(self, channels=128, blocks=8):
        super().__init__()
        self.stem = nn.Sequential \
        (
            nn.Conv2d(17, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        )
        self.res = nn.Sequential(*(ResidualBlock(channels) for _ in range(blocks)))
        self.head = nn.Sequential \
        (
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(channels, 1),
            nn.Tanh(),
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.res(x)
        return self.head(x)

class ValueNetDataset(Dataset):
    def __init__(self, states, values):
        self.states = torch.from_numpy(states).float()
        self.values = torch.from_numpy(values).float()

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return self.states[idx], self.values[idx]
    
def add_safe_globals():
    torch.serialization.add_safe_globals \
    ([
        ValueNetwork,
        nn.modules.conv.Conv2d, 
        nn.modules.batchnorm.BatchNorm2d, 
        nn.modules.activation.ReLU,
        nn.modules.pooling.AdaptiveAvgPool2d,
        nn.modules.linear.Linear,
        nn.modules.activation.Tanh,
        nn.modules.container.Sequential,
        ResidualBlock,
        nn.modules.flatten.Flatten
    ])



def train(model, dataloader, epochs=10, lr=1e-3, device=None):
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    loss = 0
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for states, targets in dataloader:
            states = states.to(device)
            targets = targets.to(device).unsqueeze(1)

            optimizer.zero_grad()
            outputs = model(states)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * states.size(0)

        avg_loss = running_loss / len(dataloader.dataset)
        loss += avg_loss
        print(f"Epoch {epoch}/{epochs} — Loss: {avg_loss:.4f}")
    return loss / epochs
