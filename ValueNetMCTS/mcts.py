from collections import namedtuple
import chess
import copy
import math
import random
import network
import torch

State = namedtuple('State', ['board', 'turn'])

players = ['White', 'Black']

class Node:
    def __init__(self, state, parent=None, parent_action=None):

        self.state = state
        self.parent = parent
        self.parent_action = parent_action

        self.children = {}
        

        self.untried_moves = chess.get_legal_moves(state.board, players[state.turn])
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
    action = random.choice(tuple(node.untried_moves))
    node.untried_moves.remove(action)
    new_state = copy.deepcopy(node.state)
    chess.play_move(new_state.board, action)
    new_state = new_state._replace(turn=1 - new_state.turn)
    new_node = Node(new_state, parent=node, parent_action=action)
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

def get_tensor(state):
    piece_indexes = {'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K':5, 'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k':11}
    board_tensor = torch.zeros((13, 8, 8))
    for row in range(len(state.board)):
        for col in range(len(state.board[row])):
            piece = state.board[row][col]
            if piece != ' ':
                board_tensor[piece_indexes[piece], row, col] = 1
    board_tensor[12, :, :] = state.turn
    return board_tensor

def MCTS(root, value_net, simulations=50000):
    for _ in range(simulations):
        node = select(root)
        leaf = expand(node) if node.untried_moves else node
        result = value_net.forward(get_tensor(leaf.state))
        backprop(leaf, result)
    return max(root.children.items(), key=lambda x: x[1].N)[0]