import yaml
import importlib
import engine.core as core
from engine.value_functions import Value
from engine.policy_functions import Policy
from concurrent.futures import ThreadPoolExecutor


class Engine:
    def __init__(self, config):
        with open(config, 'r') as file:
            self.config = yaml.safe_load(file)
            self.backend = importlib.import_module(f"engine.games.{self.config['game']}.{self.config['backend']}")
            self.value = Value(self.config.get('value_function'), **self.config.get('value', {}))
            self.policy = Policy(name=self.config.get('policy_function', None), **self.config.get('policy', {}))
            init_state = self.backend.create_init_state()
            self.states = [init_state] * self.config.get('threads', 1)

    def add_game(self, init_state=None):
        state = init_state or self.backend.create_init_state()
        self.states.append(state)
        return len(self.states) - 1
    
    def get_state(self, idx=0):
        return self.states[idx]

    def play_move(self, move, idx=0):
        new_state = self.backend.play_move(self.states[idx], move)
        self.states[idx] = new_state
        return self._evaluate(new_state)
    
    def play_moves_parallel(self, moves, max_workers=None):
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.play_move, mv, idx): idx
                for idx, mv in moves.items()
            }
            for future in futures:
                idx = futures[future]
                results[idx] = future.result()
        return results

    def play_mcts(self, idx=0, simulations=1000, c=1.4):
        state = self.states[idx]
        move = core.get_move(state, self.value, self.policy, self.backend, simulations, c)
        return self.play_move(move, idx)
    
    def play_mcts_parallel(self, idxs, simulations=1000, c=1.4, max_workers=None):        
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.play_mcts, idx, simulations, c): idx
                for idx in idxs
            }
            for future in futures:
                idx = futures[future]
                results[idx] = future.result()
        return results
        
    def _evaluate(self, state):
        if self.backend.check_win(state):
            return state.turn * 2 - 1
        if self.backend.check_draw(state):
            return 0
        return None
            


