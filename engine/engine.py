import yaml
import importlib
import engine.core as core
from engine.value_functions import Value
from engine.policy_functions import Policy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence, Callable

@dataclass
class History:
    states: list[Any] = field(default_factory=list)
    result: Optional[int] = None

class Engine:
    # ---------------------------------------------------------------------
    #  Construction
    # ---------------------------------------------------------------------
    def __init__(self, config: str | dict, *, value_functions: Sequence[Callable] | None = None):
        if isinstance(config, str):
            with open(config, 'r') as file:
                self.config = yaml.safe_load(file)
        else:
            self.config = config

        self.backend = importlib.import_module(f"engine.games.{self.config['game']}.{self.config['backend']}")
        self.policy = Policy(name=self.config.get("policy_functions"), **self.config.get("policy", {}))

        if value_functions is None:
            val = Value(self.config.get('value_function'), **self.config.get('value', {}))
            self.values = [val, val]
        else:
            if len(value_functions) != 2:
                raise ValueError("value_functions must have length 2")
            self.values = list(value_functions)

        init_state = self.backend.create_init_state()
        self.threads = self.config.get('threads', 1)
        self.states = [init_state for _ in range(self.threads)]
        self.history = [History(states=[init_state], result=None) for _ in range(self.threads)]

    # ---------------------------------------------------------------------
    #  Basic Functions
    # ---------------------------------------------------------------------
    def add_game(self, init_state=None):
        state = init_state or self.backend.create_init_state()
        self.states.append(state)
        self.history.append(History(states=[state], result=None))
        return len(self.states) - 1
    
    def get_state(self, idx=0):
        return self.states[idx]
    
    def get_hist(self, idx=0):
        return list(self.history[idx])
    
    # ------------------------------------------------------------------
    #  Dataset Helper
    # ------------------------------------------------------------------
    def get_dataset(self):
        import numpy as np
        state_arrays = []
        labels = []

        for hist_entry in self.history:
            states_seq = hist_entry.states
            final_result = hist_entry.result
            if final_result is None:
                continue

            factor = 0 if final_result == 0 else -1
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
        results_np = np.array(labels, dtype=np.float32)

        return states_np, results_np

    # ------------------------------------------------------------------
    #  Game‑play Helpers
    # ------------------------------------------------------------------
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
            futures = {executor.submit(self.play_move, mv, idx): idx for idx, mv in moves.items()}
            for future in futures:
                idx = futures[future]
                results[idx] = future.result()
        return results

    def play_mcts(self, idx=0, simulations=1000, c=1.4):
        state = self.states[idx]

        terminal_result = self._evaluate(state)
        if terminal_result is not None:
            self.history[idx].result = terminal_result
            return terminal_result

        value_fn = self.values[state.turn]
        move = core.get_move(state, value_fn, self.policy, self.backend, simulations, c)
        return self.play_move(move, idx)
    
    def play_mcts_parallel(self, idxs, simulations=1000, c=1.4, max_workers=None):        
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.play_mcts, idx, simulations, c): idx for idx in idxs}
            for future in futures:
                idx = futures[future]
                results[idx] = future.result()
        return results
    
    def reset_all_games(self):
        init_state = self.backend.create_init_state()
        self.states  = [init_state for _ in range(self.threads)]
        self.history = [History(states=[init_state], result=None) for _ in range(self.threads)]

    # ------------------------------------------------------------------
    #  Internal Helpers
    # ------------------------------------------------------------------
    def _evaluate(self, state):
        if self.backend.check_win(state):
            return state.turn * 2 - 1
        if self.backend.check_draw(state):
            return 0
        return None
    
            


