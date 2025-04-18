import os
import mcts

ROWS = 6
COLS = 7

def create_board():
    return [[' ' for _ in range(COLS)] for _ in range(ROWS)]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_board(board):
    clear_screen()
    print('  ' + '   '.join(str(i) for i in range(1, COLS + 1)))
    print('+' + '---+' * COLS)
    for row in board:
        print('|' + '|'.join(f' {cell} ' for cell in row) + '|')
        print('+' + '---+' * COLS)

def get_move(player_token):
    prompt = f"Player {player_token} — choose column (1–{COLS}) or 'q' to quit: "
    while True:
        choice = input(prompt).strip().lower()
        if choice == 'q':
            return None
        if choice.isdigit():
            col = int(choice)
            if 1 <= col <= COLS:
                return col - 1
        print(f"Invalid input. Enter 1–{COLS} or 'q'.")

def drop_token(board, col, token):
    for row in reversed(board):
        if row[col] == ' ':
            row[col] = token
            return True
    return False

def check_win(board, token):
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

def is_tie(board):
    return all(cell != ' ' for row in board for cell in row)

def get_legal_moves(board):
    return {i for i in range(7) if board[0][i] == ' '}

def main():
    board = create_board()
    tokens = ['X', 'O']
    turn = 0

    while True:
        print_board(board)
        token = tokens[turn]

        col = None
        if turn == 0:
            col = mcts.MCTS(mcts.Node(mcts.State(board, 0)))
        else:
            col = get_move(token)
        if col is None:
            print("\nGood game! Exiting…")
            break

        if not drop_token(board, col, token):
            print(f"Column {col+1} is full. Try another one.")
            input("Press Enter to continue…")
            continue

        if check_win(board, token):
            print_board(board)
            print(f"\nPlayer {token} wins! Congratulations!")
            break

        if is_tie(board):
            print_board(board)
            print("\nIt's a tie!")
            break

        turn = 1 - turn

if __name__ == '__main__':
    main()
