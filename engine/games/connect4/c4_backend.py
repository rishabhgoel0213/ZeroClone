from collections import namedtuple
import numpy as np

State = namedtuple('State', ['board', 'turn'])

ROWS = 6
COLS = 7

tokens = ['X', 'O']

def create_init_state():
    return State([[' ' for _ in range(COLS)] for _ in range(ROWS)], 0)

def play_move(state, move):
    new_board = [row.copy() for row in state.board]
    turn      = state.turn

    for row in reversed(new_board):
        if row[move[0]] == ' ':
            row[move[0]] = tokens[turn]
            break

    return state._replace(board=new_board, turn=1-turn)

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

def state_to_tensor(state):
    current_token = tokens[state.turn]
    opp_token     = tokens[1 - state.turn]

    board_arr = np.array(state.board)

    current_plane  = (board_arr == current_token).astype(np.float32)
    opponent_plane = (board_arr == opp_token).astype(np.float32)

    return np.stack([current_plane, opponent_plane], axis=0)


