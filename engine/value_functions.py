import threading
import queue
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

class Value:
    def __init__(self, name, **kwargs):
        self.name = name
        self.init_args = kwargs
        init_ref = getattr(self, f"init_{self.name}", None)
        if init_ref is not None:
            init_ref()

    def __call__(self, state, **kwargs):
        method_ref = getattr(self, self.name)
        return method_ref(state, self.init_args | kwargs)
    
    def batch(self, states, **kwargs):
        if not hasattr(self, "_req_q"):
            return [self(state, **kwargs) for state in states]

        backend = kwargs["backend"]
        out_qs  = []
        for s in states:
            arr = backend.state_to_tensor(s)
            q   = queue.Queue()
            self._req_q.put((arr, q))
            out_qs.append(q)

        return [q.get()[0] for q in out_qs]


    def random_rollout(self, state, args):
        import random
        backend = args['backend']
        inital_turn = state.turn
        while not backend.check_win(state) and not backend.check_draw(state):
            state = backend.play_move(state, random.choice(list(backend.get_legal_moves(state))))
        if backend.check_win(state):
            loser = state.turn
            return -1 if loser == inital_turn else 1
        else:
            return 0



    def crude_chess_score(self, state, args):
        backend = args['backend']
        if backend.check_win(state):
            return 1000
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9}
        factor = state.turn * -2 + 1
        return factor * sum([piece_values.get(chr(p), 0) for p in state.board])

    
    # ================================================================== #
    #  Neural-network modes (batched on a background thread)
    # ================================================================== #
    def _nn_setup(self, model, batch_size: int):
        self.model = model
        self.device = DEVICE
        self.dtype = DTYPE
        self.model.to(device=self.device, dtype=self.dtype).eval()
        self.batch_size = batch_size
        self._req_q = queue.Queue()
        t = threading.Thread(target=self._batch_worker, daemon=True)
        t.start()

    def _nn_forward(self, state, args):
        arr = args['backend'].state_to_tensor(state)
        tens = torch.tensor(arr, device=self.device, dtype=self.dtype)
        out_q = queue.Queue()
        self._req_q.put((tens, out_q))
        return out_q.get()[0]

    def _batch_worker(self):
        while True:
            arr, out_q = self._req_q.get()
            batch = [(arr, out_q)]

            for _ in range(self.batch_size - 1):
                try:
                    batch.append(self._req_q.get_nowait())
                except queue.Empty:
                    break

            import numpy as np

            arrays, out_queues = zip(*batch)
            batch_np = np.stack(arrays, axis=0)
            batch_tensor = torch.from_numpy(batch_np).to(device=self.device, dtype=self.dtype)

            with torch.no_grad():
                outputs = self.model(batch_tensor).cpu().tolist()

            for q, out in zip(out_queues, outputs):
                q.put(out)


    def init_network_latest(self):
        import os
        import models.core as core
        import torch
        module, latest_path = core.get_value_network(self.init_args['model_type'])
        ValueNetwork = getattr(module, "ValueNetwork")
        globals_fn = getattr(module, "add_safe_globals")
        globals_fn()
        model = ValueNetwork() if not os.path.exists(latest_path) else torch.load(latest_path, map_location=DEVICE)
        self._nn_setup(model, self.init_args.get('batch_size', 1))

    def network_latest(self, state, args):
        return self._nn_forward(state, args)


    
    def init_network_at_path(self):
        import os, models.core as core
        path = self.init_args['path']
        module, _ = core.get_value_network(self.init_args['model_type'])
        getattr(module, "add_safe_globals")()
        ValueNetwork = getattr(module, "ValueNetwork")

        model = ValueNetwork() if not os.path.exists(path) else torch.load(path, map_location=DEVICE)
        self._nn_setup(model, self.init_args.get('batch_size', 1))
    
    def network_at_path(self, state, args):
        return self._nn_forward(state, args)
        
