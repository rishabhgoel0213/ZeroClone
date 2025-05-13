from collections import namedtuple
import random

State = namedtuple('State', ['board', 'turn'])

ROWS = 6
COLS = 7

tokens = ['X', 'O']

def create_init_state():
    return State([[' ' for _ in range(COLS)] for _ in range(ROWS)], 0)


def play_move(state, move):
    def copy_state(state):
        return state._replace(board=[row.copy() for row in state.board], turn=1-state.turn)

    new_state = copy_state(state)
    for row in reversed(new_state.board):
        if row[move[0]] == ' ':
            row[move[0]] = tokens[new_state.turn]
            return new_state

def check_win(state):
    board = state.board
    token = tokens[1 - state.turn]
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == token for i in range(4)):
                return True
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == token for i in range(4)):
                return True
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == token for i in range(4)):
                return True
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == token for i in range(4)):
                return True
    return False

def check_draw(state):
    return all(cell != ' ' for row in state.board for cell in row)

def get_legal_moves(state):
    return {(i, 0)  for i in range(COLS) if state.board[0][i] == ' '}

def get_value(state):
    turn_copy = state.turn
    while not check_win(state) and not is_tie(state):
        state = play_move(state, random.choice(list(get_legal_moves(state))))

    if check_draw(state):
        return 0
    else:
        return -1 if state.turn == turn_copy else 1


