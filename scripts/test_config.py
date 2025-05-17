from engine.engine import Engine
import argparse
import os


def simulate_config(args):
    path = f"{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/configs/{args.config}.yaml"
    engine = Engine(path)

    unfinished = set(range(len(engine.states)))

    final_states = [[] * len(engine.states)]
    final_results = [None] * len(engine.states)

    while unfinished:
        print("\nCurrent board state:")
        print(engine.states)

        sims = engine.config['mcts']['simulations']
        c = engine.config['mcts']['c_puct']
        print(f"Bot is thinking ({sims} sims, c={c})...")

        results = engine.play_mcts_parallel(idxs=list(unfinished), simulations=sims, c=c)

        finished =  [(results[i], i) for i in unfinished if results[i] is not None]
        for r, i in finished:
            unfinished.remove(i)
            final_results[i] = r
    return final_results



for r, i in final_results:
    print(f"Game {i + 1} result:")
    if r == 0:
        print(f"Its is a draw!")
    else:
        winner = 'Player 1' if r == 1 else 'Player 2'
        print(f"Winner: {winner}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Game engine for simulating games between player and MCTS algorithm"
    )
    parser.add_argument(
        "-c", "--config",
        metavar="FILE",
        required=True,
        help="name of config being used"
    )
    args = parser.parse_args()

    