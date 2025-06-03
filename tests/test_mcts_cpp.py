import subprocess, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import importlib
import random

import pytest

from engine.value_functions import Value
from engine.policy_functions import Policy
from engine.games.connect4 import c4_backend as backend
from engine import core as pycore


@pytest.fixture(scope="module", autouse=True)
def build_extension():
    subprocess.run([sys.executable, 'setup.py', 'build_ext', '--inplace'], cwd=os.path.join('engine','mcts_cpp'), check=True)
    importlib.invalidate_caches()
    if 'engine.mcts_cpp' in sys.modules:
        importlib.reload(sys.modules['engine.mcts_cpp'])


def test_cpp_matches_python_move():
    random.seed(0)
    state = backend.create_init_state()
    val = Value('random_rollout')
    pol = Policy()
    py_move = pycore._get_move_python(state, val, pol, backend, simulations=20, c=1.4)
    random.seed(0)
    from engine.mcts_cpp import get_move as cpp_move
    cpp_mv = cpp_move(state, val, pol, backend, 20, 1.4, 32)
    assert cpp_mv in backend.get_legal_moves(state)
