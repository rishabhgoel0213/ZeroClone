# ZeroClone

## Project Overview
**ZeroClone** is a general game-playing AI engine inspired by DeepMind’s AlphaZero. It combines **Monte Carlo Tree Search (MCTS)** with deep neural networks to learn strong play through self-play.  
The framework is modular (new games can be added by implementing a small backend interface) while offering high-performance C++ back-ends for existing games (currently **Chess** and **Connect Four**).

## Installation

> **The only officially tested setup method is via Docker.**  
> A helper script both **builds** the image **and** launches an interactive container.

### Prerequisites
* **Docker** ≥ 20.10  
* **NVIDIA Container Toolkit** *(optional, but required for GPU acceleration)*

### One-Line Setup
```bash
./build_and_run.sh           # builds image and drops you into a bash shell inside it
````

* Builds an image tagged `zeroclone` from `server/Dockerfile`.
* Starts a container with the repo mounted and GPU passthrough (`--gpus all`) if available.

## Usage

### 1. Self-Play & Training

```bash
python scripts/train.py -c configs/connect4.yaml    # Connect Four config
python scripts/train.py -c configs/chess_value.yaml # Chess config
```

Tweak MCTS sims, network depth, etc. in the corresponding `configs/*.yaml`.

### 2. Programmatic Engine Access

```python
from engine.engine import Engine
eng = Engine("configs/connect4.yaml")
state = eng.play_mcts(idx=0, simulations=800)   # one strong move
```

### 3. REST API (FastAPI server)

#### 3-step quick-start

```bash
# 1 – (be sure you’re inside the running container)
python server/main.py -c configs/connect4.yaml --host 0.0.0.0 --port 8000 &

# 2 – hit the endpoints from your host
curl -X POST http://localhost:8000/add_game                  # -> {"idx":0}

curl -X POST http://localhost:8000/play_move \
     -H "Content-Type: application/json" \
     -d '{"idx": 0, "move": 3}'                         # play column 3

curl -X POST http://localhost:8000/play_mcts \
     -H "Content-Type: application/json" \
     -d '{"idx": 0, "simulations": 800, "c": 1.4}'

curl http://localhost:8000/state/0                           # board snapshot
```

> **Tip:** Prefer [HTTPie](https://httpie.io/) for a friendlier CLI, or use the PHP files in the frontend folder to interact with the existing games via GUI:
>
> ```bash
> http POST :8000/add_game
> http POST :8000/play_move idx:=0 move:='3'
> ```

## Technologies Used

* **Python 3**  ·  **PyTorch**  ·  **Monte Carlo Tree Search**
* **C++ / PyBind11** back-ends for speed-critical game logic
* **FastAPI** for serving games over HTTP
* **Docker** for reproducible, GPU-ready environments

## Contributing

1. **Fork** → **Branch** → **PR**.  Keep commits focused & descriptive.
2. Ensure `pytest` passes and `./build_and_run.sh` still works.
3. Document new configs and add tests when adding features or new games.

Feel free to open an issue for bug reports or feature requests.

## License

Released under the **MIT License** — see `LICENSE` for full text.
