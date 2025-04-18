from collections import namedtuple
import connect4 as c4
import copy
import math
import random

State = namedtuple('State', ['board', 'turn'])

class Node:
    def __init__(self, state, parent=None, parent_action=None):

        self.state = state
        self.parent = parent
        self.parent_action = parent_action

        self.children = {}
        

        self.untried_moves = c4.get_legal_moves(state.board)
        self.Na = dict.fromkeys(self.untried_moves, 0)
        self.Wa = dict.fromkeys(self.untried_moves, 0.0)
        self.Qa = dict.fromkeys(self.untried_moves, 0.0)
        self.N = 0


tokens = ['X', 'O']

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
    action = random.choice(tuple(node.untried_moves))
    node.untried_moves.remove(action)
    new_state = copy.deepcopy(node.state)
    c4.drop_token(new_state.board, action, tokens[new_state.turn])
    new_state = new_state._replace(turn=1 - new_state.turn)
    new_node = Node(new_state, parent=node, parent_action=action)
    node.children[action] = new_node
    return new_node

def simulate(state):
    board = copy.deepcopy(state.board)
    turn = state.turn
    while True:
        if c4.check_win(board, tokens[turn]):
            return -1 if state.turn == turn else 1
        if c4.is_tie(board):
            return 0
        turn = 1 - turn
        action = random.choice(tuple(c4.get_legal_moves(board)))
        c4.drop_token(board, action, tokens[turn])

def backprop(node, result):
    node.N += 1
    if node.parent is not None:
        parent = node.parent
        a = node.parent_action
        parent.Na[a] += 1
        parent.Wa[a] += result
        parent.Qa[a] = parent.Wa[a] / parent.Na[a]
        backprop(parent, -result)


def MCTS(root, simulations=1000):
    for _ in range(simulations):
        node = select(root)
        leaf = expand(node) if node.untried_moves else node
        result = simulate(leaf.state)
        backprop(leaf, result)
    return max(root.children.items(), key=lambda x: x[1].N)[0]