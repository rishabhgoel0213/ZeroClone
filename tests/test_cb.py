import pytest
from engine.games.chess import chess_backend as backend

def print_board_from_fen(fen: str) -> None:
    # Extract piece placement field
    piece_placement = fen.split()[0]
    rows = piece_placement.split('/')
    
    # File labels
    files = '  a b c d e f g h'
    print(files)
    
    for rank_idx, row in enumerate(rows):
        rank = 8 - rank_idx
        expanded = ''
        for c in row:
            if c.isdigit():
                expanded += '.' * int(c)
            else:
                expanded += c
        # Print with spaces between
        print(f"{rank} " + ' '.join(expanded) + f" {rank}")
    
    print(files)
    # Optionally, print side to move and castling rights:
    parts = fen.split()
    if len(parts) >= 3:
        print(f"Side to move: {'White' if parts[1]=='w' else 'Black'}; Castling: {parts[2]}")


# ---------------------------------------------------------------------------
#  Basic sanity‑check tests for the chess backend
# ---------------------------------------------------------------------------

def test_initial_position_legal_moves_count():
    """The initial chess position must have **exactly 20** legal moves (white)."""
    state = backend.create_init_state()
    moves = backend.get_legal_moves(state)
    assert isinstance(moves, list), "get_legal_moves should return a list"
    assert len(moves) == 20, f"Expected 20 legal moves, got {len(moves)}"


def test_initial_position_no_win_or_draw():
    """No win or draw should be detected in the starting position."""
    state = backend.create_init_state()
    assert backend.check_win(state) is False, "check_win() should be False at start"
    assert backend.check_draw(state) is False, "check_draw() should be False at start"


def test_play_move_turn_flip():
    """After a legal move the `turn` field must flip from 0 → 1 or 1 → 0."""
    state = backend.create_init_state()
    initial_turn = state.turn
    first_move = backend.get_legal_moves(state)[0]
    new_state = backend.play_move(state, first_move)
    assert new_state.turn == 1 - initial_turn, (
        f"Turn not flipped correctly: expected {1 - initial_turn}, got {new_state.turn}"
    )


def test_state_to_tensor_shape():
    """`state_to_tensor` should return an array‑like with shape (planes, 8, 8)."""
    state = backend.create_init_state()
    tensor = backend.state_to_tensor(state)
    assert hasattr(tensor, "shape"), "Return value missing .shape attribute"
    assert tensor.ndim == 3, f"Tensor must be 3‑D, got {tensor.ndim}‑D"
    assert tensor.shape[1:] == (8, 8), f"Spatial dims must be 8×8, got {tensor.shape[1:]}"

# ---------------------------------------------------------------------------
#  Edge‑case positions hard‑coded via FEN
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fen, is_win, is_draw", 
[
    ("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1", True, False),
    ("r1bqkbnr/ppp2Qpp/n2p4/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 1", True, False),
    ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", False, True),
    ("8/8/8/8/8/8/2n5/2K4k w - - 0 1", False, True),
    ("8/8/8/1k6/8/8/4K3/5B2 w - - 0 1", False, True)
])
def test_fen_endings(fen, is_win, is_draw):
    state = backend.state_from_fen(fen)
    assert backend.check_win(state) is is_win
    assert backend.check_draw(state) is is_draw
