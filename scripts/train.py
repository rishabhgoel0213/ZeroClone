from __future__ import annotations

import argparse
import contextlib
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import torch
from torch.utils.data import DataLoader

from engine.engine import Engine
import models.core as core

# ──────────────────────────────────────────────────────────────────────────
#  Logging helper – duplicate stdout/stderr to a timestamped file
# ──────────────────────────────────────────────────────────────────────────
def _init_logfile() -> Path:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"train_{ts}.log"

    class _Tee:
        def __init__(self, *streams):
            self._streams = streams
        def write(self, data):
            for s in self._streams:
                s.write(data)
                s.flush()
        def flush(self):
            for s in self._streams:
                s.flush()

    _fh = open(log_path, "w", buffering=1)
    sys.stdout = _Tee(sys.stdout, _fh)
    sys.stderr = _Tee(sys.stderr, _fh)
    print(f"[LOGFILE] → {log_path.resolve()}", flush=True)
    return log_path


_logfile_path = _init_logfile()

CSV_WRITER = csv.writer(sys.stdout, lineterminator="\n")


def emit_stats(**kv):
    now = int(time.time())
    keys = ["ts"] + sorted(kv)
    values = [now] + [kv[k] for k in sorted(kv)]
    CSV_WRITER.writerow(values)
    sys.stdout.flush()

import os
emit_stats(stage="pid", pid=os.getpid())

@contextlib.contextmanager
def timer(label):
    t0 = time.time()
    yield
    print(f"{label:<20} : {time.time() - t0:6.2f} s")


# ──────────────────────────────────────────────────────────────────────────
#  NN training helper
# ──────────────────────────────────────────────────────────────────────────
def train_and_save_latest(
    model_type: str,
    states: torch.Tensor,
    values: torch.Tensor,
    *,
    epochs: int = 10,
    lr: float = 1e-4,
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 8,
) -> float:

    module, latest_path = core.get_value_network(model_type)

    ValueNetDataset = getattr(module, "ValueNetDataset")
    dataset = ValueNetDataset(states, values)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)

    ValueNetwork = getattr(module, "ValueNetwork")
    train_fn = getattr(module, "train")

    if Path(latest_path).exists():
        model = torch.load(latest_path, map_location="cuda")
        print("Loaded existing net from", latest_path)
    else:
        model = ValueNetwork()
        print("No previous model – created new network instance")

    avg_loss = train_fn(model, loader, epochs, lr)

    checkpoint_dir = Path(latest_path).parent / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    if Path(latest_path).exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        Path(latest_path).rename(checkpoint_dir / f"{ts}.pth")

    torch.save(model, latest_path)
    print("Saved new *latest* model to", latest_path)
    return avg_loss


# ──────────────────────────────────────────────────────────────────────────
#  Self-play helpers
# ──────────────────────────────────────────────────────────────────────────
def simulate_games(engine: Engine, total_games: int, current_cycle: int) -> List[int | None]:
    unfinished = set(range(min(total_games, engine.threads)))
    final = [None] * min(total_games, engine.threads)

    while unfinished:
        sims = engine.config["mcts"]["simulations"]
        c_val = engine.config["mcts"]["c_puct"]
        results = engine.play_mcts_parallel(list(unfinished), simulations=sims, c=c_val)

        finished_now = [(results[i], i) for i in unfinished if results[i] is not None]
        for res, idx in finished_now:
            unfinished.remove(idx)
            final[idx] = res
            emit_stats(stage="game_done", cycle=current_cycle, finished=sum(r is not None for r in final), target=total_games)

            if len(final) < total_games:
                final += [None]
                unfinished.add(engine.add_game())

    return final


def schedule_hyperparams \
(
    cycle: int,
    *,
    games_cap: int = 2000,
    sims_cap: int = 800,
    init_lr: float = 3e-4,
    lr_decay: float = 0.95,
    lr_floor: float = 1e-5,
) -> Dict[str, Any]:

    games = min(games_cap, 500 * (cycle + 1))
    sims = int(min(100 * (1.2 ** cycle), sims_cap))
    c_val = max(1.25, 2.5 * (0.97 ** cycle))
    lr = max(init_lr * (lr_decay ** cycle), lr_floor)
    return {"games": games, "simulations": sims, "c_puct": c_val, "lr": lr}


def full_training_run \
(
    config_path: str,
    *,
    cycles: int = 30,
    batch_size: int = 256,
    epochs: int = 4,
    num_workers: int = 8,
    games_cap: int = 2000,
    sims_cap: int = 800,
    init_lr: float = 3e-4,
    lr_decay: float = 0.95,
    lr_floor: float = 1e-5,
) -> None:

    engine = Engine(config_path)
    loss_acc = 0.0

    for cycle in range(cycles):
        engine.reset_all_games()

        hp = schedule_hyperparams(cycle, games_cap=games_cap, sims_cap=sims_cap, init_lr=init_lr, lr_decay=lr_decay, lr_floor=lr_floor)
        engine.config["mcts"]["simulations"] = hp["simulations"]
        engine.config["mcts"]["c_puct"] = hp["c_puct"]

        emit_stats \
        (
            stage="cycle_start",
            cycle=cycle + 1,
            total_cycles=cycles,
            games_target=hp["games"],
            sims=hp["simulations"],
        )
        with timer("SELF-PLAY"):
            simulate_games(engine, hp["games"], cycle + 1)

        with timer("DATASET BUILD"):
            states, values = engine.get_dataset()
        print(f"Collected {len(values)} training positions")

        with timer("TRAIN"):
            loss_acc += train_and_save_latest \
            (
                engine.config["value"]["model_type"],
                states,
                values,
                epochs=epochs,
                lr=hp["lr"],
                batch_size=batch_size,
                num_workers=num_workers,
            )

    emit_stats(stage="train_done", cycle=cycles, loss=loss_acc / cycles, epochs=epochs)


# ──────────────────────────────────────────────────────────────────────────
#  CLI entry-point
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Self-play + value-net trainer (dynamic scheduling, reset-per-cycle)")

    # Hyper-params
    ap.add_argument("-c", "--config", required=True, help="Config name (without .yaml) under ./configs/")
    ap.add_argument("--cycles", type=int, default=30, help="Number of cycles")
    ap.add_argument("--batch-size", type=int, default=256, help="DataLoader batch size")
    ap.add_argument("--epochs", type=int, default=4, help="Epochs per cycle")
    ap.add_argument("--num-workers", type=int, default=8, help="DataLoader workers")

    # Tuning
    ap.add_argument("--games-cap", type=int, default=2000)
    ap.add_argument("--sims-cap", type=int, default=800)
    ap.add_argument("--init-lr", type=float, default=3e-4)
    ap.add_argument("--lr-decay", type=float, default=0.95)
    ap.add_argument("--lr-floor", type=float, default=1e-5)

    args = ap.parse_args()

    full_training_run \
    (
        args.config,
        cycles=args.cycles,
        batch_size=args.batch_size,
        epochs=args.epochs,
        num_workers=args.num_workers,
        games_cap=args.games_cap,
        sims_cap=args.sims_cap,
        init_lr=args.init_lr,
        lr_decay=args.lr_decay,
        lr_floor=args.lr_floor,
    )
