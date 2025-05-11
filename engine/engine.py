import yaml
import importlib
import core
from value_functions import Value
from policy_functions import Policy



import os, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)



class Engine:
    def __init__(self, config):
        with open(config, 'r') as file:
            self.config = yaml.safe_load(file)
            self.backend = importlib.import_module(f"engine.games.{self.config['game']}.{self.config['backend']}")
            self.state = self.backend.create_init_state()
            self.value = Value(self.config.get('value_function'), **self.config.get('value', {}))
            self.policy = Policy(name=self.config.get('policy_function', None), **self.config.get('policy', {}))

    def play_move(self, move):
        self.state = self.backend.play_move(self.state, move)
        if self.backend.check_win(self.state):
            return self.state.turn * 2 - 1
        if self.backend.check_draw(self.state):
            return 0

    def play_mcts(self, simulations=1000, c=1.4):
        self.state = self.backend.play_move(self.state, core.get_move(self.state, self.value, self.policy, self.backend, simulations, c))
        if self.backend.check_win(self.state):
            return self.state.turn * 2 - 1
        if self.backend.check_draw(self.state):
            return 0
        
if __name__ == "__main__":
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
    while True:
        print("\nCurrent board state:")
        print(engine.state)

        # choice = input("Choose move: manual (m) or bot (b)? [m/b]: ").strip().lower()
        # if choice == 'm':
        #     move_input = input("Enter your move: ").strip()
        #     try:
        #         move = engine.backend.parse_move(engine.state, move_input)
        #     except AttributeError:
        #         move = move_input
        #     result = engine.play_move(move)
        # else:
        sims = engine.config.get('mcts').get('simulations')
        c_val = engine.config.get('mcts').get('c_puct')
        print(f"Bot is thinking ({sims} sims, c={c_val})...")
        result = engine.play_mcts(simulations=sims, c=c_val)

        if result is not None:
            print("\nGame over! ", end='')
            if result == 0:
                print("Its a draw!")
            else:
                winner = 'Black' if result == -1 else 'White'
                print(f"Winner: {winner}")
            break


