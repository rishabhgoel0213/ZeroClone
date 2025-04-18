import torch
import torch.nn as nn
import torch.nn.functional as F

class Network(nn.Module):
    def __init__(self):  # e.g. [10, 20, 30, 5]
        super().__init__()
        self.layers = nn.ModuleList()
        self.layers.append(nn.Flatten())
        for in_size, out_size in zip(layer_sizes[:-1], layer_sizes[1:]):
            self.layers.append(nn.Linear(in_size, out_size))

    def forward(self, x):
        for layer in self.layers[:-1]:
            x = F.relu(layer(x))
        return self.layers[-1](x)
