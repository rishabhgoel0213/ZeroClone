import math
import random

try:
    from .mcts_cpp import get_move as _cpp_get_move
except Exception:  # pragma: no cover - extension optional
    _cpp_get_move = None

class _PyNode:
    def __init__(self, state, moves, parent=None, parent_action=None):
        self.state = state
        self.parent = parent
        self.parent_action = parent_action

        self.children = {}

        self.untried_moves = list(moves)
        self.Na = dict.fromkeys(self.untried_moves, 0)
        self.Wa = dict.fromkeys(self.untried_moves, 0.0)
        self.Qa = dict.fromkeys(self.untried_moves, 0.0)
        self.N = 0

def _UCT(node, action, c):
    if node.Na[action] == 0:
        return float("inf")
    return node.Qa[action] + c*math.sqrt(math.log(node.N) / node.Na[action])

def _select(node, c):
    if node.untried_moves:
        return node
    if not node.children:
        return node
    return _select(node.children[max(node.children, key=lambda action: _UCT(node, action, c))], c)

def _expand(node, backend, policy):
    action = policy(node.untried_moves)
    node.untried_moves.remove(action)

    new_state = backend.play_move(node.state, action)
    new_moves = backend.get_legal_moves(new_state)
    new_node = _PyNode(new_state, new_moves, parent=node, parent_action=action)

    node.children[action] = new_node
    return new_node

def _backprop(node, result):
    node.N += 1
    if node.parent is not None:
        parent = node.parent
        a = node.parent_action
        parent.Na[a] += 1
        parent.Wa[a] -= result
        parent.Qa[a] = parent.Wa[a] / parent.Na[a]
        _backprop(parent, -result)

def _get_move_python(state, value, policy, backend, simulations=1000, c=1.4, batch_size=32):
    root = _PyNode(state, backend.get_legal_moves(state))

    pending_nodes = []
    pending_states = []

    def flush():
        if not pending_nodes:
            return
        values = value.batch(pending_states, backend=backend)
        for node, v in zip(pending_nodes, values):
            _backprop(node, v)
        pending_nodes.clear()
        pending_states.clear()

    for _ in range(simulations):
        node = _select(root, c)
        leaf = _expand(node, backend, policy) if node.untried_moves else node

        pending_nodes.append(leaf)
        pending_states.append(leaf.state)

        if len(pending_nodes) >= batch_size:
            flush()

    flush()

    return max(root.children.items(), key=lambda kv: kv[1].N)[0]

def get_move(state, value, policy, backend, simulations=1000, c=1.4, batch_size=32):
    """Return best move using either C++ or Python implementation."""
    if _cpp_get_move is not None:
        try:
            return _cpp_get_move(state, value, policy, backend, simulations, c, batch_size)
        except Exception:
            pass
    return _get_move_python(state, value, policy, backend, simulations, c, batch_size)
