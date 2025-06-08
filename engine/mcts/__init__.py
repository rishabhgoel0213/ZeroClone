from importlib import import_module

try:
    mcts = import_module('.mcts', __name__)
    get_move = mcts.get_move
except Exception:
    mcts = None
    def get_move(*args, **kwargs):
        raise ImportError('mcts_cpp extension not built')
