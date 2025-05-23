# ZeroClone

## Project Overview

**ZeroClone** is a general game‑playing AI engine inspired by DeepMind’s AlphaZero. It combines **Monte Carlo Tree Search (MCTS)** with deep neural networks to learn strong play through self‑play. The framework is modular—new games can be added by implementing a small backend interface—while offering high‑performance C++ back‑ends for existing games (currently **Chess** and **Connect Four**).

## Installation

> **The only officially tested setup method is via Docker.** The repository includes a helper script that both **builds** the Docker image **and** drops you into a ready‑to‑use container.

### Prerequisites

* **Docker** (≥ 20.10)
* **NVIDIA Container Toolkit** *(optional, but required for GPU acceleration)*

### One‑Line Setup

```bash
./build_and_run.sh               # builds image and starts an interactive container
```

The script will:

1. Build an image tagged `zeroclone` using the Dockerfile in `server/`.
2. Start an interactive container with the current repository mounted inside and—if available—your GPU passed through (via `--gpus all`).

Once inside the container you can immediately run training or play games without any extra steps.

> **Tip 🛠️**  If you exit the container and want to re‑enter it later, use `docker start -ai zeroclone_dev` (the script names the container `zeroclone_dev`).

## Usage

### Self‑Play & Training

Run a self‑play session followed by value‑network training, using the YAML config of your choice:

```bash
python scripts/train.py -c connect4          # Connect Four example
python scripts/train.py -c chess_value       # Chess example
```

Adjust parameters (MCTS sims, network depth, etc.) by editing `configs/*.yaml`.

### Programmatic Engine Use

```python
from engine.engine import Engine
eng = Engine("configs/connect4.yaml")
state = eng.play_mcts(idx=0, simulations=800)   # play one high‑quality move
```

See `examples/` for more detailed notebooks and scripts.

## Technologies Used

* **Python 3**  ·  **PyTorch**  ·  **Monte Carlo Tree Search**
* **C++ / PyBind11** back‑ends for speed‑critical game logic
* **FastAPI** *(planned)* for serving games over HTTP
* **Docker** for reproducible, GPU‑ready environments

## Contributing

1. **Fork** → **Branch** → **PR**.  Keep commits focused and descriptive.
2. Ensure `pytest` passes and `./build_and_run.sh` still works.
3. Document new config options and add tests when adding features or new games.

Feel free to open an issue for bug reports or feature requests.

## License

Released under the **MIT License** — see `LICENSE` for full text.
