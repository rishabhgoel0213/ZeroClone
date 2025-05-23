import threading
import queue
import torch

class Value:
    def __init__(self, name, **kwargs):
        self.name = name
        self.init_args = kwargs
        init_ref = getattr(self, f"init_{self.name}", None)
        if init_ref is not None:
            return init_ref()

    def __call__(self, state, **kwargs):
        method_ref = getattr(self, self.name)
        return method_ref(state, self.init_args | kwargs)



    def random_rollout(self, state, args):
        import random
        backend = args['backend']
        inital_turn = state.turn
        while not backend.check_win(state) and not backend.check_draw(state):
            state = backend.play_move(state, random.choice(list(backend.get_legal_moves(state))))
        if backend.check_win(state):
            if state.turn == inital_turn:
                return -1
            else:
                return 1
        else:
            return 0



    def crude_chess_score(self, state, args):
        backend = args['backend']
        if backend.check_win(state):
            return 1000
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9}
        factor = state.turn * 2 - 1
        return factor * sum([piece_values.get(chr(p), 0) for p in state.board])

    

    def init_network_latest(self):
        import os
        import engine.core as core
        module, latest_path = core.get_value_network(self.init_args['model_type'])
        ValueNetwork = getattr(module, "ValueNetwork")
        self.model = ValueNetwork() if not os.path.exists(latest_path) else torch.load(latest_path, map_location="cpu")

        self.model.to('cuda').eval()
        self.batch_size = self.init_args.get('batch_size', 1)
        self._req_queue = queue.Queue()
        self._worker = threading.Thread(target=self._batch_worker, daemon=True)
        self._worker.start()

    def _batch_worker(self):
        while True:
            tensor, out_q = self._req_queue.get()
            batch = [(tensor, out_q)]

            for _ in range(self.batch_size - 1):
                try:
                    tup = self._req_queue.get_nowait()
                    batch.append(tup)
                except queue.Empty:
                    break      
                      
            tensors, out_queues = zip(*batch)
            batch_tensor = torch.stack(tensors, dim=0)

            with torch.no_grad():
                outputs = self.model(batch_tensor).cpu().tolist()

            for out_q, out in zip(out_queues, outputs):
                out_q.put(out)

    def network_latest(self, state, args):
        arr = args['backend'].state_to_tensor(state)
        tensor = torch.tensor(arr, device='cuda')
        resp_q = queue.Queue()
        self._req_queue.put((tensor, resp_q))
        return resp_q.get()[0]
        
