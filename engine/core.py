import math
import random

class Node:
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

def UCT(node, action, c):
    if node.Na[action] == 0:
        return float("inf")
    return node.Qa[action] + c*math.sqrt(math.log(node.N) / node.Na[action])

def select(node, c):
    if node.untried_moves:
        return node
    if not node.children:
        return node
    return select(node.children[max(node.children, key=lambda action: UCT(node, action, c))], c)

def expand(node, backend, policy):
    action = policy(node.untried_moves)
    node.untried_moves.remove(action)

    new_state = backend.play_move(node.state, action)
    new_moves = backend.get_legal_moves(new_state)
    new_node = Node(new_state, new_moves, parent=node, parent_action=action)

    node.children[action] = new_node
    return new_node

def backprop(node, result):
    node.N += 1
    if node.parent is not None:
        parent = node.parent
        a = node.parent_action
        parent.Na[a] += 1
        parent.Wa[a] += result
        parent.Qa[a] = parent.Wa[a] / parent.Na[a]
        backprop(parent, -result)

def get_move(state, value, policy, backend, simulations=1000, c=1.4):
    root = Node(state, backend.get_legal_moves(state))
    for _ in range(simulations):
        node = select(root, c)
        leaf = expand(node, backend, policy) if node.untried_moves else node
        result = value(leaf.state, backend=backend)
        backprop(leaf, result)
    return max(root.children.items(), key=lambda x: x[1].N)[0]