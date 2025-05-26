from __future__ import annotations

import argparse, importlib, yaml
from typing import Callable, Sequence

from engine.engine import Engine
from engine.value_functions import Value
import models.core as mcore

# --------------------------------------------------------------------- #
#  Helpers                                                              #
# --------------------------------------------------------------------- #

def simulate(engine: Engine, total: int) -> Sequence[int]:
    unfinished = set(range(min(total, engine.threads)))
    results = [None] * min(total, engine.threads)

    while unfinished:
        sims = engine.config['mcts']['simulations']
        c = engine.config['mcts']['c_puct']
        partial = engine.play_mcts_parallel(list(unfinished), sims, c)

        for idx in list(unfinished):
            if partial[idx] is not None:
                print("Game finished")
                results[idx] = partial[idx]
                unfinished.remove(idx)
                if len(results) < total:
                    results += [None]
                    unfinished.add(engine.add_game())
    return results

def win_rate(results: Sequence[int], latest_is_white: bool) -> float:
    wins = draws = 0
    for r in results:
        if (latest_is_white and r == 1) or (not latest_is_white and r == -1):
            wins += 1
        elif r == 0:
            draws += 1
    return (wins + 0.5 * draws) / len(results)

def evaluate_pair(cfg: dict, latest_v: Callable, other_v: Callable, games: int) -> float:
    g_white = games // 2
    g_black = games - g_white

    eng_w = Engine(cfg, value_functions=[latest_v, other_v])
    wr_w  = win_rate(simulate(eng_w, g_white), latest_is_white=True)

    eng_b = Engine(cfg, value_functions=[other_v, latest_v])
    wr_b  = win_rate(simulate(eng_b, g_black), latest_is_white=False)

    return (wr_w * g_white + wr_b * g_black) / games

# --------------------------------------------------------------------- #
#  Main                                                                 #
# --------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", required=True, help="YAML config")
    ap.add_argument("-n", "--games",  type=int, default=10, help="Games per match-up")
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    importlib.import_module(f"engine.games.{cfg['game']}.{cfg['backend']}")

    model_type = cfg["value"]["model_type"]
    batch_size = cfg["value"].get("batch_size", 1)

    ckpts = mcore.list_checkpoints(model_type)
    if not ckpts:
        raise RuntimeError(f"No checkpoints found for {model_type}")

    first_ckpt, prev_ckpt = ckpts[0], ckpts[-1]

    v_latest = Value("network_latest", model_type=model_type, batch_size=batch_size)
    v_first = Value("network_at_path", model_type=model_type, path=str(first_ckpt), batch_size=batch_size)
    v_prev = Value("network_at_path", model_type=model_type, path=str(prev_ckpt), batch_size=batch_size)

    print(f"Evaluating {model_type}  –  {args.games} games each match-up\n")
    wr_first = evaluate_pair(cfg, v_latest, v_first, args.games)
    wr_prev = evaluate_pair(cfg, v_latest, v_prev,  args.games)

    print("Win-rates for *latest* network")
    print("--------------------------------")
    print(f"vs first checkpoint : {wr_first:.2%}")
    print(f"vs prev  checkpoint : {wr_prev :.2%}")

if __name__ == "__main__":
    main()
