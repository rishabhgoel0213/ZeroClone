import os
import mcts

FILES = 'abcdefgh'
RANKS = '12345678'


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


def print_board(board):
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


def get_move(player_color):
    prompt = f"Player {player_color} — enter move (e.g. e2 e4) or 'q' to quit: "
    while True:
        choice = input(prompt).strip().lower()
        if choice == 'q':
            return None
        parts = choice.split()
        if len(parts) == 2:
            from_sq = parse_square(parts[0])
            to_sq = parse_square(parts[1])
            if from_sq and to_sq:
                return from_sq, to_sq
        print("Invalid input. Enter moves like 'e2 e4' or 'q' to quit.")

def play_move(board, action):
    (fr, fc), (tr, tc) = action
    board[tr][tc] = board[fr][fc]
    board[fr][fc] = ' '

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


def get_legal_moves(board, player_color):
    moves = set()
    directions = {
        'P': [(-1, 0), (-1, -1), (-1, 1)],
        'p': [(1, 0), (1, -1), (1, 1)],
        'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
        'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
        'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
        'Q': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
        'K': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
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
                        moves.add(((r, c), (nr, nc)))
                        if (r == 6 and key == 'P') or (r == 1 and key == 'p'):
                            nr2 = r + dr * 2
                            if in_bounds(nr2, nc) and is_empty(board[nr2][nc]):
                                moves.add(((r, c), (nr2, nc)))
                    elif dc != 0 and is_opponent(board[nr][nc], player_color):
                        moves.add(((r, c), (nr, nc)))
            elif p in ('N', 'K'):
                for dr, dc in directions[p]:
                    nr, nc = r + dr, c + dc
                    if not in_bounds(nr, nc):
                        continue
                    if is_empty(board[nr][nc]) or is_opponent(board[nr][nc], player_color):
                        moves.add(((r, c), (nr, nc)))
            elif p in ('B', 'R', 'Q'):
                for dr, dc in directions[p]:
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc):
                        if is_empty(board[nr][nc]):
                            moves.add(((r, c), (nr, nc)))
                        elif is_opponent(board[nr][nc], player_color):
                            moves.add(((r, c), (nr, nc)))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc
    return moves


def game_winner(board):
    has_white = any(piece == 'K' for row in board for piece in row)
    has_black = any(piece == 'k' for row in board for piece in row)
    if not has_black:
        return 'White'
    if not has_white:
        return 'Black'
    return None


def main():
    board = create_board()
    player = 'White'
    while True:
        print_board(board)
        winner = game_winner(board)
        if winner:
            print(f"\n{winner} wins by capturing the king!")
            break
        moves = get_legal_moves(board, player)
        if not moves:
            print("\nStalemate! It's a draw.")
            break

        if player == 'Black':
            user_move = get_move(player)
        else:
            user_move = mcts.MCTS(mcts.Node(mcts.State(board, 0)))

        if user_move is None:
            print("\nGood game! Exiting…")
            break
        if user_move not in moves:
            print("\nIllegal move. Try again.")
            input("Press Enter to continue…")
            continue
        play_move(board, user_move)
        player = 'Black' if player == 'White' else 'White'

if __name__ == '__main__':
    main()
