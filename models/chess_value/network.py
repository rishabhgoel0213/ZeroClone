import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset
import numpy as np

class ValueNetwork(nn.Module):
    def __init__(self):
        super(ValueNetwork, self).__init__()
        self.conv1 = nn.Conv2d(17, 32, kernel_size=3, padding=1)
        self.bn1   = nn.BatchNorm2d(32)
        self.relu  = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2   = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.bn3   = nn.BatchNorm2d(64)
        self.pool  = nn.AdaptiveAvgPool2d(1)
        self.fc    = nn.Linear(64, 1)
        self.tanh  = nn.Tanh()

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        x = self.tanh(x)
        return x

class ValueNetDataset(Dataset):
    def __init__(self, states, values):
        self.states = torch.from_numpy(states).float()
        self.values = torch.from_numpy(values).float()

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return self.states[idx], self.values[idx]
    
def add_safe_globals():
    torch.serialization.add_safe_globals([
        ValueNetwork,
        nn.modules.conv.Conv2d, 
        nn.modules.batchnorm.BatchNorm2d, 
        nn.modules.activation.ReLU,
        nn.modules.pooling.AdaptiveAvgPool2d,
        nn.modules.linear.Linear,
        nn.modules.activation.Tanh
    ])



def train(model, dataloader, epochs=10, lr=1e-3, device='cuda'):
    model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

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
        print(f"Epoch {epoch}/{epochs} — Loss: {avg_loss:.4f}")
