from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import torch
from torch.utils.data import DataLoader

from engine.engine import Engine
import models.core as core


def train_and_save_latest(model_type: str,
                          states: torch.Tensor,
                          values: torch.Tensor,
                          *,
                          epochs: int = 10,
                          lr: float = 1e-4,
                          batch_size: int = 32,
                          shuffle: bool = True,
                          num_workers: int = 8) -> None:

    module, latest_path = core.get_value_network(model_type)

    ValueNetDataset = getattr(module, "ValueNetDataset")
    dataset = ValueNetDataset(states, values)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)

    ValueNetwork = getattr(module, "ValueNetwork")
    train_fn      = getattr(module, "train")

    if Path(latest_path).exists():
        model = torch.load(latest_path, map_location="cpu")
        print("Loaded existing net from", latest_path)
    else:
        model = ValueNetwork()
        print("No previous model – created new network instance")

    train_fn(model, loader, epochs, lr)

    checkpoint_dir = Path(latest_path).parent / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    if Path(latest_path).exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        Path(latest_path).rename(checkpoint_dir / f"{ts}.pth")

    torch.save(model, latest_path)
    print("Saved new *latest* model to", latest_path)


def simulate_games(engine: Engine, total_games: int) -> List[int | None]:
    unfinished = set(range(min(total_games, engine.threads)))
    final: List[int | None] = [None] * total_games

    while unfinished:
        sims = engine.config['mcts']['simulations']
        c_val = engine.config['mcts']['c_puct']
        results = engine.play_mcts_parallel(list(unfinished), simulations=sims, c=c_val)

        finished_now = [(results[i], i) for i in unfinished if results[i] is not None]
        for res, idx in finished_now:
            unfinished.remove(idx)
            final[idx] = res

            if len(final) < total_games:
                unfinished.add(engine.add_game())

    return final


def schedule_hyperparams(cycle: int,
                         *,
                         games_cap: int = 2000,
                         sims_cap: int = 800,
                         init_lr: float = 3e-4,
                         lr_decay: float = 0.95,
                         lr_floor: float = 1e-5) -> Dict[str, Any]:
    
    games = min(games_cap, 500 * (cycle + 1))
    sims  = int(min(100 * (1.2 ** cycle), sims_cap))
    c_val = max(1.25, 2.5 * (0.97 ** cycle))
    lr    = max(init_lr * (lr_decay ** cycle), lr_floor)
    return {"games": games, "simulations": sims, "c_puct": c_val, "lr": lr}


def full_training_run(config_path: str,
                      *,
                      cycles: int = 30,
                      batch_size: int = 256,
                      epochs: int = 4,
                      num_workers: int = 8,
                      games_cap: int = 2000,
                      sims_cap: int = 800,
                      init_lr: float = 3e-4,
                      lr_decay: float = 0.95,
                      lr_floor: float = 1e-5) -> None:

    engine = Engine(config_path)

    for cycle in range(cycles):
        print("\n============================")
        print(f" CYCLE {cycle + 1}/{cycles}")
        print("============================")

        engine.reset_all_games()

        hp = schedule_hyperparams(cycle,
                                   games_cap=games_cap,
                                   sims_cap=sims_cap,
                                   init_lr=init_lr,
                                   lr_decay=lr_decay,
                                   lr_floor=lr_floor)
        engine.config['mcts']['simulations'] = hp['simulations']
        engine.config['mcts']['c_puct']      = hp['c_puct']

        print(f"▶ Self‑play: {hp['games']} games  "
              f"({hp['simulations']} sims | c={hp['c_puct']:.2f})")
        simulate_games(engine, hp['games'])

        states, values = engine.get_dataset()
        print(f"Collected {len(values)} training positions")

        print(f"▶ Training: {epochs} epochs | lr={hp['lr']:.2e}")
        train_and_save_latest(engine.config['value']['model_type'],
                              states,
                              values,
                              epochs=epochs,
                              lr=hp['lr'],
                              batch_size=batch_size,
                              num_workers=num_workers)

    print("\n…Training campaign complete – latest model saved!…")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Self‑play + value‑net trainer (dynamic scheduling, reset‑per‑cycle)"
    )

    #Hyperparams
    ap.add_argument("-c", "--config", required=True, help="Config name (without .yaml) located under ./configs/")
    ap.add_argument("--cycles", type=int, default=30, help="Number of cycles (default 30)")
    ap.add_argument("--batch-size", type=int, default=256, help="DataLoader batch size")
    ap.add_argument("--epochs", type=int, default=4, help="Epochs per cycle")
    ap.add_argument("--num-workers", type=int, default=8, help="DataLoader workers")

    #Tuning arguments
    ap.add_argument("--games-cap", type=int, default=2000)
    ap.add_argument("--sims-cap", type=int, default=800)
    ap.add_argument("--init-lr", type=float, default=3e-4)
    ap.add_argument("--lr-decay", type=float, default=0.95)
    ap.add_argument("--lr-floor", type=float, default=1e-5)

    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    cfg_path  = repo_root / "configs" / f"{args.config}.yaml"

    full_training_run(str(cfg_path),
                      cycles=args.cycles,
                      batch_size=args.batch_size,
                      epochs=args.epochs,
                      num_workers=args.num_workers,
                      games_cap=args.games_cap,
                      sims_cap=args.sims_cap,
                      init_lr=args.init_lr,
                      lr_decay=args.lr_decay,
                      lr_floor=args.lr_floor)
