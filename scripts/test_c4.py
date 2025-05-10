from engine.games.connect4 import c4_backend as c4
from engine import core
from engine.value_functions import Value
from engine.policy_functions import Policy
import os


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_board(board):
    clear_screen()
    print('  ' + '   '.join(str(i) for i in range(1, c4.COLS + 1)))
    print('+' + '---+' * c4.COLS)
    for row in board:
        print('|' + '|'.join(f' {cell} ' for cell in row) + '|')
        print('+' + '---+' * c4.COLS)

def get_move(player_token):
    prompt = f"Player {player_token} — choose column (1–{c4.COLS}) or 'q' to quit: "
    while True:
        choice = input(prompt).strip().lower()
        if choice == 'q':
            return None
        if choice.isdigit():
            col = int(choice)
            if 1 <= col <= c4.COLS:
                return (col - 1, 0)
        print(f"Invalid input. Enter 1–{c4.COLS} or 'q'.")

def play_bot():
    state = c4.create_init_state()
    value = Value(name="random_rollout")
    policy = Policy()
    while True:
        print_board(state.board)
        token = c4.tokens[state.turn]            
        moves = c4.get_legal_moves(state)
        move = core.get_move(state, value, policy, c4)
        state = c4.play_move(state, move)
        if c4.check_win(state):
            print(f"\nPlayer {token} wins! Congratulations!")
            break
        if c4.check_draw(state):
            print("\nIt's a tie!")
            break

if __name__ == "__main__": 
    play_bot()