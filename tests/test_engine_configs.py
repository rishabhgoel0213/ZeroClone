import os, sys, subprocess, importlib, glob
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Build C++ extensions required for the engine
subprocess.run([sys.executable, 'setup.py', 'build_ext', '--inplace'], cwd=os.path.join('engine','games','chess'), check=True)
subprocess.run([sys.executable, 'setup.py', 'build_ext', '--inplace'], cwd=os.path.join('engine','mcts'), check=True)
importlib.invalidate_caches()

from engine.engine import Engine
import engine.mcts as mcts

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'configs')
CONFIGS = glob.glob(os.path.join(CONFIG_DIR, '*.yaml'))

@pytest.mark.parametrize('cfg', CONFIGS)
def test_engine_config_basic_move(cfg):
    eng = Engine(cfg)
    moves = eng.legal_moves()
    assert len(moves) > 0
    mcts.get_move(eng.get_state(), eng.values[0], eng.policy, eng.backend, 1, eng.config['mcts']['c_puct'], 1)

