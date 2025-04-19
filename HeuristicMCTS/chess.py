import os
import mcts
from collections import namedtuple
from stockfish import Stockfish

FILES = 'abcdefgh'
RANKS = '12345678'
PLAYERS = ['White', 'Black']

State = namedtuple('State', ['board', 'turn', 'white_can_castle_king', 'white_can_castle_queen', 'black_can_castle_king', 'black_can_castle_queen'])

piece_values = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K':50,
    'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9, 'k':-50
}

def create_board():
    board = [[' ' for _ in range(8)] for _ in range(8)]
    placement = ['r','n','b','q','k','b','n','r']
    for i, p in enumerate(placement):
        board[0][i] = p
        board[1][i] = 'p'
        board[6][i] = 'P'
        board[7][i] = p.upper()
    return board


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_board(state):
    board = state.board
    clear_screen()
    print('    ' + '   '.join(FILES))
    print('  +' + '---+' * 8)
    for r in range(8):
        row = board[r]
        print(f"{8-r} | " + ' | '.join(cell if cell != ' ' else '.' for cell in row) + ' |')
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
                return from_sq, to_sq, -abs(piece_values.get(state.board[to_sq[0]][to_sq[1]], 0))
        print("Invalid input. Enter moves like 'e2 e4' or 'q' to quit.")

def play_move(state, action):
    board = [row[:] for row in state.board]
    turn = 1 - state.turn
    white_can_castle_king = state.white_can_castle_king
    white_can_castle_queen = state.white_can_castle_queen
    black_can_castle_king = state.black_can_castle_king
    black_can_castle_queen = state.black_can_castle_queen
    
    (fr, fc), (tr, tc), value = action
    if board[fr][fc] == 'K' or (board[fr][fc] == 'R' and fc == 7):
        white_can_castle_king = False
    if board[fr][fc] == 'K' or (board[fr][fc] == 'R' and fc == 0):
        white_can_castle_queen = False
    if board[fr][fc] == 'k' or (board[fr][fc] == 'r' and fc == 7):
        black_can_castle_king = False
    if board[fr][fc] == 'k' or (board[fr][fc] == 'r' and fc == 0):
        black_can_castle_king = False

    if board[fr][fc] == 'K' and tc - fc == 2:
        board[7][5] = 'R'
        board[7][7] = ' '
    elif board[fr][fc] == 'k' and tc - fc == 2:
        board[0][5] = 'r'
        board[0][7] = ' '
    elif board[fr][fc] == 'K' and tc - fc == -2:
        board[7][3] = 'R'
        board[7][0] = ' '
    elif board[fr][fc] == 'k' and tc - fc == -2:
        board[0][3] = 'r'
        board[0][0] = ' '

    board[tr][tc] = board[fr][fc]
    board[fr][fc] = ' '

    if tr == 0 and board[tr][tc] == 'P':
        board[tr][tc] = 'Q'
    elif tr == 7 and board[tr][tc] == 'p':
        board[tr][tc] = 'q'

    new_state = State(board, turn, white_can_castle_king, white_can_castle_queen, black_can_castle_king, black_can_castle_queen)
    return new_state

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def is_opponent(piece, player_color):
    if piece == ' ':
        return False
    if player_color == 'White':
        return piece.islower()
    else:
        return piece.isupper()


def is_empty(piece):
    return piece == ' '

def attacks_on_square(state, r, c):
    board = state.board
    attack_map = {}
    if board[r][c] == ' ':
        return attack_map
    player = PLAYERS[0 if board[r][c].isupper() else 1]
    directions = {
        'P': [(1, 1), (1, -1)],
        'p': [(-1, 1), (-1, -1)],
        'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
        'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
        'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
        'Q': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
        'K': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
    }
    for piece in directions.keys():
        for dr, dc in directions[piece]:
            if in_bounds(r + dr, c + dc) and piece == 'P' and is_opponent('P', player) and board[r + dr][c + dc] == piece:
                attack_map.setdefault('P', [])
                attack_map['P'] += [(r + dr, c + dc)]
            elif in_bounds(r + dr, c + dc) and piece == 'p' and is_opponent('p', player) and board[r + dr][c + dr] == piece:
                attack_map.setdefault('p', [])
                attack_map['p'] += [(r + dr, c + dc)]
            elif in_bounds(r + dr, c + dc) and piece in ('N', 'K') and piece == board[r + dr][c + dc].upper() and is_opponent(board[r + dr][c + dc], player):
                attack_map.setdefault(board[r + dr][c + dc], [])
                attack_map[board[r + dr][c + dc]] += [(r + dr, c + dc)]
            elif piece in ('B', 'R', 'Q'):
                nr, nc = r + dr, c + dc
                while in_bounds(nr, nc):
                    if piece == board[nr][nc].upper() and is_opponent(board[nr][nc], player):
                        attack_map.setdefault(board[r + dr][c + dc], [])
                        attack_map[board[r + dr][c + dc]] += [(r + dr, c + dc)]
                        break
                    elif board[nr][nc] == ' ':
                        nr += dr
                        nc += dc
                    else:
                        break
    return attack_map

def king_under_attack(state, player):
    for r in range(8):
        for c in range(8):
            if (state.board[r][c] == 'K' and player == 'White') or (state.board[r][c] == 'k' and player == 'Black'):
                return attacks_on_square(state, r, c)

def get_legal_moves(state):
    board = state.board
    player_color = PLAYERS[state.turn]
    moves = set()
    directions = {
        'P': [(-1, 0), (-1, -1), (-1, 1)],
        'p': [(1, 0), (1, -1), (1, 1)],
        'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
        'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
        'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
        'Q': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
        'K': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1), (0, 2), (0, -2)],
    }
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == ' ':
                continue
            if player_color == 'White' and not piece.isupper():
                continue
            if player_color == 'Black' and not piece.islower():
                continue
            p = piece.upper()
            if p == 'P':
                key = piece
                for dr, dc in directions[key]:
                    nr, nc = r + dr, c + dc
                    if not in_bounds(nr, nc):
                        continue
                    if dc == 0 and is_empty(board[nr][nc]):
                        moves.add(((r, c), (nr, nc), 0))
                        if (r == 6 and key == 'P') or (r == 1 and key == 'p'):
                            nr2 = r + dr * 2
                            if in_bounds(nr2, nc) and is_empty(board[nr2][nc]):
                                moves.add(((r, c), (nr2, nc), 0))
                    elif dc != 0 and is_opponent(board[nr][nc], player_color):
                        moves.add(((r, c), (nr, nc), -abs(piece_values[board[nr][nc]])))
            elif p == 'K':
                for dr, dc in directions[p]:
                    nr, nc = r + dr, c + dc
                    if piece == 'K':
                        if dc == 2 and (not state.white_can_castle_king or not is_empty(board[nr][nc - 1])):
                            continue
                        elif dc == -2 and (not state.white_can_castle_queen or not is_empty(board[nr][nc + 1] or not is_empty(board[nr][nc + 3]))):
                            continue
                    elif piece == 'k':
                        if dc == 2 and (not state.black_can_castle_king or not is_empty(board[nr][nc - 1])):
                            continue
                        elif dc == -2 and (not state.black_can_castle_queen or not is_empty(board[nr][nc + 1] or not is_empty(board[nr][nc + 3]))):
                            continue
                    if not in_bounds(nr, nc):
                        continue
                    if is_empty(board[nr][nc]):
                        moves.add(((r, c), (nr, nc), 0))
                    elif is_opponent(board[nr][nc], player_color):
                        moves.add(((r, c), (nr, nc), -abs(piece_values[board[nr][nc]])))
            elif p == 'N':
                for dr, dc in directions[p]:
                    nr, nc = r + dr, c + dc
                    if not in_bounds(nr, nc):
                        continue
                    if is_empty(board[nr][nc]):
                        moves.add(((r, c), (nr, nc), 0))
                    elif is_opponent(board[nr][nc], player_color):
                        moves.add(((r, c), (nr, nc), -abs(piece_values[board[nr][nc]])))
            elif p in ('B', 'R', 'Q'):
                for dr, dc in directions[p]:
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc):
                        if is_empty(board[nr][nc]):
                            moves.add(((r, c), (nr, nc), 0))
                        elif is_opponent(board[nr][nc], player_color):
                            moves.add(((r, c), (nr, nc), -abs(piece_values[board[nr][nc]])))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc
    invalid_moves = set()
    for move in moves:
        state_copy = play_move(state, move)
        if king_under_attack(state_copy, PLAYERS[state.turn]):
            invalid_moves.add(move)
    moves.difference_update(invalid_moves)
    return moves


def game_winner(state):
    board = state.board
    has_white = any(piece == 'K' for row in board for piece in row)
    has_black = any(piece == 'k' for row in board for piece in row)
    if not has_black:
        return 'White'
    if not has_white:
        return 'Black'
    return None

def fen_string_generator(state):
    board = state.board
    fen_rows = []
    for row in board:
        empty = 0
        fen_row = ""
        for square in row:
            if square == " ":
                empty += 1
            else:
                if empty:
                    fen_row += str(empty)
                    empty = 0
                fen_row += square
        if empty:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    placement = "/".join(fen_rows)
    to_move = 'w' if state.turn == 0 else 'b'
    castling_rights = 'K' if state.white_can_castle_king else '' + 'Q' if state.white_can_castle_queen else '' + 'k' if state.black_can_castle_king else '' + 'q' if state.black_can_castle_queen else ''
    return placement + ' ' + to_move + ' ' + ' - 0 1'

def main():
    board = create_board()
    turn = 0;
    state = State(board, turn, True, True, True, True)
    stockfish = Stockfish(path="/workspaces/alphazero-dev/stockfish", parameters={
        "UCI_LimitStrength": True,
        "UCI_Elo": 1320,
        "Skill Level": 0
    })
    while True:
        print_board(state)
        winner = game_winner(state)
        moves = get_legal_moves(state)
        if not moves and king_under_attack(state, PLAYERS[state.turn]):
            print(f"\n{PLAYERS[1 - state.turn]} wins by checkmate!")
            break
        elif not moves:
            print("\nStalemate! It's a draw.")
            break

        stockfish.set_fen_position(fen_string_generator(state))
        s = stockfish.get_best_move()
        from_sq = parse_square(s[:2])
        to_sq = parse_square(s[2:4])
        stockfish_move = (from_sq, to_sq, -abs(piece_values.get(state.board[to_sq[0]][to_sq[1]], 0)))

        user_move = mcts.MCTS(mcts.Node(state)) if turn == 0 else stockfish_move
        # user_move = get_move(state) if turn == 0 else get_move(state)
        # user_move = mcts.MCTS(mcts.Node(state)) if turn == 0 else get_move(state)
        # user_move = stockfish_move if turn == 0 else get_move(state)

        if user_move is None:
            print("\nGood game! Exiting…")
            break
        if user_move not in moves and king_under_attack(state, PLAYERS[state.turn]):
            print("\nYour king is under attack! Try again.")
            input("Press Enter to continue…")
            continue
        elif user_move not in moves:
            print("\nIllegal move. Try again.")
            input("Press Enter to continue…")
            continue
        state = play_move(state, user_move)
        turn = 1 - turn

if __name__ == '__main__':
    main()
