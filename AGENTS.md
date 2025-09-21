# ZeroClone – Agent Guide

You are already inside the project’s Docker environment. The repo has been set up via `build_and_run.sh`; compilers, Python deps, and native extensions are available. Do not re‑provision the system or reinstall packages unless explicitly requested.

This guide lists the day‑to‑day workflows, key paths, and practical knobs for working on chess with a value network.

## What’s Ready
- Python env with PyTorch (CPU) is active.
- Native extensions (chess backend, MCTS) are built and importable.
- Editable install is in place; local code changes take effect immediately.

## Common Tasks
- Run all tests from repo root:
  - `pytest -q`
  - Tests compile both the chess backend and the MCTS extension on the fly.

- Start a training run (self‑play + value net):
  - `python scripts/train.py -c configs/chess_value.yaml --cycles 5 --batch-size 256 --epochs 4`
  - For a managed background run with live view/kill:
    - Start: `python scripts/train_manager.py -c configs/chess_value.yaml -- --cycles 5`
    - View:  `python scripts/train_manager.py --view`

- Evaluate latest model vs checkpoints:
  - `python scripts/evaluate.py -c configs/chess_value.yaml -n 20`
  - Requires at least one saved checkpoint under `models/chess_value/checkpoints/`.

## Key Files & Paths
- Configs:
  - `configs/chess_value.yaml` — chess with value-only setup (MCTS + random policy).

- Engine & MCTS:
  - `engine/engine.py` — core orchestration (self‑play, dataset build, MCTS hooks).
  - `engine/mcts` — C++ MCTS core (`mcts.get_move`).
  - `engine/games/chess` — C++ chess backend and bindings.

- Value network (chess):
  - `models/chess_value/network.py` — architecture, dataset wrapper, train loop.
  - Latest model: `models/chess_value/latest.pth`
  - Checkpoints: `models/chess_value/checkpoints/*.pth`

- Scripts:
  - `scripts/train.py` — full training cycles with dynamic scheduling and replay.
  - `scripts/train_manager.py` — background run + log viewer (simple TUI).
  - `scripts/evaluate.py` — win‑rate vs early/previous checkpoints.

## Logs & Monitoring
- Training writes CSV‑style progress lines to `./logs/train_*.log`.
- `train_manager.py --view` tails the newest log, shows cycle progress, and can kill by typing `k` + ENTER.

## Practical Knobs (Value‑Only Chess)
- `threads` (in config): number of parallel self‑play games. Tune to CPU cores.
- `mcts.simulations` and `mcts.c_puct`: search depth/temperature. Higher sims increase quality but slow self‑play.
- `value.batch_size` (in config): micro‑batch for background network inference during MCTS. Smaller values reduce latency; larger values improve throughput when many games run in parallel.
- Training CLI flags (`scripts/train.py`): `--cycles`, `--batch-size`, `--epochs`, `--num-workers`, and learning‑rate schedule controls. See the script’s `argparse` for defaults.

## Rebuilding Native Extensions (Only If Needed)
- Chess backend: `engine/games/chess/build.sh`
- MCTS backend:  `engine/mcts/build.sh`
- Tests will also rebuild as necessary; prefer running `pytest` to validate builds.

## Conventions
- Keep changes focused and minimal; ensure tests pass (`pytest -q`).
- Avoid introducing heavy dependencies or GPU‑only features; this environment is CPU‑only.
- When changing training behavior, update configs and scripts coherently and document the change inline or in PR notes.

## Quick Sanity Checks
- Import paths:
  - `python -c "from engine.engine import Engine; Engine('configs/chess_value.yaml')"`
- Single MCTS step:
  - `python -c "from engine.engine import Engine; e=Engine('configs/chess_value.yaml'); e.play_mcts()"`

If anything deviates from the above (imports fail, extensions missing), prefer running the relevant build script or `pytest -q` to surface and auto‑rebuild where applicable.
