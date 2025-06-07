from importlib import import_module

try:
    mcts_cpp = import_module('.mcts_cpp', __name__)
    get_move = mcts_cpp.get_move
except Exception:  # pragma: no cover - compiled module may be absent
    mcts_cpp = None
    def get_move(*args, **kwargs):
        raise ImportError('mcts_cpp extension not built')
