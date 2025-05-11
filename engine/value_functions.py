class Value:
    def __init__(self, name, **kwargs):
        self.name = name
        self.args = kwargs

    def __call__(self, state, **kwargs):
        method_ref = getattr(self, self.name)
        return method_ref(state, self.args | kwargs)

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

    def network_latest(self, state, args):
        import torch
        import os
        from models.value.network import ValueNetwork
        model = ValueNetwork() if not os.path.exists(args['model_path']) else torch.load(args['model_path'], map_location="cpu")
        model.to('cuda')
        with torch.no_grad():
            arr = args['backend'].state_to_tensor(state)
            tensor = torch.tensor(arr, device='cuda')
            return model(tensor.unsqueeze(0)).item()
        
