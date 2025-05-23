import yaml
import importlib
import engine.core as core
from engine.value_functions import Value
from engine.policy_functions import Policy
from concurrent.futures import ThreadPoolExecutor
import torch
from dataclasses import dataclass, field
from typing import List, Any, Optional

@dataclass
class History:
    states: list[Any] = field(default_factory=list)
    result: Optional[int] = None


class Engine:
    def __init__(self, config):
        with open(config, 'r') as file:
            self.config = yaml.safe_load(file)
            self.backend = importlib.import_module(f"engine.games.{self.config['game']}.{self.config['backend']}")
            self.value = Value(self.config.get('value_function'), **self.config.get('value', {}))
            self.policy = Policy(name=self.config.get('policy_function', None), **self.config.get('policy', {}))
            init_state = self.backend.create_init_state()
            num_init = self.config.get('init_games', 1)
            self.states = [init_state for _ in range(num_init)]
            self.history = [History(states=[init_state], result=None) for _ in range(num_init)]

    def add_game(self, init_state=None):
        state = init_state or self.backend.create_init_state()
        self.states.append(state)
        self.history.append(History(states=[state], result=None))
        return len(self.states) - 1
    
    def get_state(self, idx=0):
        return self.states[idx]
    
    def get_hist(self, idx=0):
        return list(self.history[idx])
    
    def get_dataset(self):
        import numpy as np
        state_arrays = []
        labels = []

        for hist_entry in self.history:
            states_seq = hist_entry.states
            final_result = hist_entry.result
            if final_result is None:
                continue

            factor = -1
            label_entry = []
            for state in states_seq:
                arr = self.backend.state_to_tensor(state)
                state_arrays.append(arr.astype(np.float32))
                label_entry.append(factor)
                factor = -factor
            labels += list(reversed(label_entry))

        if not state_arrays:
            dummy = self.backend.state_to_tensor(self.backend.get_init_state())
            empty_states = np.empty((0,) + dummy.shape, dtype=np.float32)
            empty_labels = np.empty((0,), dtype=np.float32)
            return empty_states, empty_labels
        
        states_np = np.stack(state_arrays, axis=0)
        results_np = np.array(labels, dtype=np.int64)

        return states_np, results_np

    def play_move(self, move, idx=0):
        new_state = self.backend.play_move(self.states[idx], move)
        self.states[idx] = new_state

        hist = self.history[idx]
        hist.states.append(new_state)
        hist.result = self._evaluate(new_state)
        return hist.result
    
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
            


