import chess
import math

players = ['White', 'Black']

class Node:
    def __init__(self, state, parent=None, parent_action=None):
        self.state = state
        self.parent = parent
        self.parent_action = parent_action

        self.children = {}
        

        self.untried_moves = chess.get_legal_moves(state)
        self.Na = dict.fromkeys(self.untried_moves, 0)
        self.Wa = dict.fromkeys(self.untried_moves, 0.0)
        self.Qa = dict.fromkeys(self.untried_moves, 0.0)
        self.N = 0


def UCT(node, action, c):
    if node.Na[action] == 0:
        return float("inf")
    return node.Qa[action] + c*math.sqrt(math.log(node.N) / node.Na[action])

def select(node, c=math.sqrt(2)):
    if node.untried_moves:
        return node
    if not node.children:
        return node
    return select(node.children[max(node.children, key=lambda action: UCT(node, action, c))])

def expand(node):
    sorted_moves = sorted(node.untried_moves, key=lambda x: x[2])
    action = sorted_moves[0]
    node.untried_moves.remove(action)
    new_node = Node(chess.play_move(node.state, action), parent=node, parent_action=action)
    node.children[action] = new_node
    return new_node


def simulate(state):
    score = 0
    factor = state.turn * 2 - 1
    for row in state.board:
        for piece in row:
            score += chess.piece_values.get(piece, 0) * factor
    return 0 if score == 0 else abs(score) / score

def backprop(node, result):
    node.N += 1
    if node.parent is not None:
        parent = node.parent
        a = node.parent_action
        parent.Na[a] += 1
        parent.Wa[a] += result
        parent.Qa[a] = parent.Wa[a] / parent.Na[a]
        backprop(parent, -result)


def MCTS(root, simulations=5000):
    for _ in range(simulations):
        node = select(root)
        leaf = expand(node) if node.untried_moves else node
        result = simulate(leaf.state)
        backprop(leaf, result)
    return max(root.children.items(), key=lambda x: x[1].N)[0]