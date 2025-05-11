from engine.engine import Engine
import argparse


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
path = f"/app/ZeroClone/configs/{args.config}.yaml"
engine = Engine(path)
unfinished = set(range(len(engine.states)))
final_results = []
while unfinished:
    print("\nCurrent board state:")
    print(engine.states)
    sims = engine.config.get('mcts').get('simulations')
    c_val = engine.config.get('mcts').get('c_puct')
    print(f"Bot is thinking ({sims} sims, c={c_val})...")
    results = engine.play_mcts_parallel(idxs=list(unfinished), simulations=sims, c=c_val)
    finished =  [(results[i], i) for i in unfinished if results[i] is not None]
    for r, i in finished:
        unfinished.remove(i)
        final_results.append((r, i))
for r, i in final_results:
    print(f"Game {i + 1} result:")
    if r == 0:
        print(f"Its is a draw!")
    else:
        winner = 'Player 1' if r == 1 else 'Player 2'
        print(f"Winner: {winner}")

    