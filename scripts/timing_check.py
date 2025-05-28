from __future__ import annotations

import argparse
import importlib
import time
from pathlib import Path

import yaml

import engine.core as core
from engine.policy_functions import Policy
from engine.value_functions import Value


def run_once(state, backend, value_fn, policy, sims: int, batch: int) -> float:
    t0 = time.perf_counter()
    core.get_move(state, value_fn, policy, backend, simulations=sims, c=1.4, batch_size=batch)
    return time.perf_counter() - t0


def main() -> None:
    ap = argparse.ArgumentParser(description="Time core.get_move() end-to-end")
    ap.add_argument("-c", "--config", required=True, help="YAML config file")
    ap.add_argument("--sims",  type=int, default=2048, help="MCTS playouts")
    ap.add_argument("--batch", type=int, default=32,   help="Leaf batch size")
    ap.add_argument("--loops", type=int, default=10,   help="Number of moves to time")
    args = ap.parse_args()

    cfg_path = Path(args.config).expanduser()
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    game   = cfg["game"]
    module = cfg["backend"]
    backend = importlib.import_module(f"engine.games.{game}.{module}")

    v_cfg  = cfg["value"]
    model_type  = v_cfg["model_type"]
    v_batchsize = v_cfg.get("batch_size", 1)

    value_fn = Value("network_latest", model_type=model_type, batch_size=v_batchsize)

    policy = Policy(name=cfg.get("policy_function", "random"), **cfg.get("policy", {}))

    init_state = backend.create_init_state()

    run_once(init_state, backend, value_fn, policy, args.sims, args.batch)

    times = []
    for _ in range(args.loops):
        t = run_once(init_state, backend, value_fn, policy, args.sims, args.batch)
        times.append(t)

    print(f"--- core.get_move timing ({args.loops} runs) ---")
    print(f"simulations : {args.sims}")
    print(f"batch size  : {args.batch}")
    print(f"mean  time  : {sum(times)/len(times):.3f} s")
    print(f"median time : {sorted(times)[len(times)//2]:.3f} s")


if __name__ == "__main__":
    main()
