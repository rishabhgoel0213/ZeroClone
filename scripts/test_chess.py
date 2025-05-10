import sys, os
import time

_here = os.path.dirname(__file__)
if _here not in sys.path:
    sys.path.insert(0, _here)

from engine.games.chess import chess_backend as cb
from engine import core
from engine.value_functions import Value
from engine.policy_functions import Policy
FILES = 'abcdefgh'
RANKS = '12345678'
PLAYERS = ['white', 'black']
piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9}


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_fen_string(state):
    assert all(cell in (32, 0,
                    *map(ord, 'PNBRQKpnbrqk')) for cell in state.board), "garbage in board"

    board = state.board
    if len(board) != 64:
        raise ValueError("board must have exactly 64 entries")
    fen_ranks = []
    for rank in range(8):
        empty = 0
        parts = []
        row_start = rank * 8
        for file in range(8):
            code = board[row_start + file]
            ch = chr(code)
            if ch == ' ':
                empty += 1
            else:
                if empty:
                    parts.append(str(empty))
                    empty = 0
                parts.append(ch)
        if empty:
            parts.append(str(empty))
        fen_ranks.append(''.join(parts))
    print('/'.join(fen_ranks))

def print_board(state):
    board = state.board
    clear_screen()
    print('    ' + '   '.join(FILES))
    print('  +' + '---+' * 8)
    for r in range(8):
        row = board[r * 8:r * 8 + 8]
        print(f"{8-r} | " + ' | '.join(chr(cell) if chr(cell) != ' ' else '.' for cell in row) + ' |')
        print('  +' + '---+' * 8)


def parse_square(sq):
    if len(sq) != 2:
        return None
    file, rank = sq[0], sq[1]
    if file not in FILES or rank not in RANKS:
        return None
    col = FILES.index(file)
    row = 8 - int(rank)
    return row, col


def get_move(state):
    prompt = f"Player {PLAYERS[state.turn]} — enter move (e.g. e2 e4) or 'q' to quit: "
    while True:
        choice = input(prompt).strip().lower()
        if choice == 'q':
            return None
        parts = choice.split()
        if len(parts) == 2:
            from_sq = parse_square(parts[0])
            to_sq = parse_square(parts[1])
            if from_sq and to_sq:
                return (from_sq[0], from_sq[1], to_sq[0], to_sq[1]), abs(piece_values.get(state.board[to_sq[0]*8+to_sq[1]], 0))
        print("Invalid input. Enter moves like 'e2 e4' or 'q' to quit.")


def get_value(state):
    if cb.is_repeat_draw(state):
        return 0
    if not cb.get_legal_moves(state):
        return 100 if cb.king_under_attack(state, state.turn) else 0
    return -cb.get_score(state, state.turn)


def play_bot():
    state = cb.create_init_state();
    while True:
        print_board(state)
        moves = cb.get_legal_moves(state)
        checked = cb.king_under_attack(state, state.turn)
        if not moves and checked:
            print(f"\n{PLAYERS[1 - state.turn]} wins by checkmate!")
            break
        elif not moves:
            print("\nStalemate! It's a draw.")
            break
        elif cb.is_repeat_draw(state):
            print("\nDraw by reptition!")
            break

        user_move = core.get_move(state, get_value, cb, 10000)
        print(user_move)
        if user_move is None:
            print("\nGood game! Exiting…")
            break
        if user_move not in moves:
            print("\nIllegal move. Try again.")
            if checked:
                print("\nYour king is under attack!")
            input("Press Enter to continue…")
            continue
        state = cb.play_move(state, user_move)


def play_bot2():
    import random
    state = cb.create_init_state()
    value = Value('crude_chess_score')
    policy = Policy('immediate_value', policy_freedom=3)
    while True:
        print_board(state)
        if cb.check_draw(state):
            print("\nIt's a tie!")
            break
        elif cb.check_win(state):
            print(f"\nPlayer {PLAYERS[1 - state.turn]} wins! Congratulations!")
            break
        move = get_move(state) if state.turn == 0 else core.get_move(state, value, policy, cb)
        state = cb.play_move(state, move)
        
def test_win_detection(state):
    if cb.check_draw(state):
            print("\nIt's a tie!") 
    elif cb.check_win(state):
        print(f"\nPlayer {PLAYERS[1 - state.turn]} wins! Congratulations!")
            

if __name__ == "__main__":
    play_bot2()