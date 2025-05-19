from engine.engine import Engine
import argparse
import os


def simulate_games(engine, total_games):
    threads = len(engine.states)
    unfinished = set(range(threads))
    final_results = [None for _ in range(total_games)]
    finished_count = 0

    while unfinished:
        print("\nCurrent board states:")
        out = [f"      Game {i + 1} state: {engine.states[i]}" for i in unfinished]
        for string in out:
            print(string)

        sims = engine.config['mcts']['simulations']
        c = engine.config['mcts']['c_puct']
        print(f"Bot is thinking ({sims} sims, c={c})...")

        results = engine.play_mcts_parallel(idxs=list(unfinished), simulations=sims, c=c)

        finished =  [(results[i], i) for i in unfinished if results[i] is not None]
        for r, i in finished:
            unfinished.remove(i)
            final_results[i] = r
            finished_count += 1
            if not total_games - 1 in unfinished and final_results[total_games - 1] is None:
                unfinished.add(engine.add_game())

    return final_results



def print_results(results):
    for i in range(len(results)):
        r = results[i]
        if r == 0:
            result = "Its is a draw!"
        else:
            winner = 'Player 1' if r == 1 else 'Player 2'
            result = f"{winner} won!"
        print(f"Game {i + 1} result: {result}")


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
    path = f"{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/configs/{args.config}.yaml"
    engine = Engine(path)

    results = simulate_games(engine, 4)
    print_results(results)
    states_batch, results_batch = engine.get_dataset()
    print(states_batch, results_batch)
    

    