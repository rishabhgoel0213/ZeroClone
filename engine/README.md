# Engine

This directory contains the main reinforcement-learning engine along with game-specific backends.  The engine expects each game backend to expose a minimal set of functions so that MCTS can operate without knowing any game rules.

## Adding a New Game

1. **Create a folder under `engine/games/` named after your game.**
2. **Implement a backend module** inside that folder.  A backend may be a pure Python file or a PyBind11 extension written in C++.  The module **must** provide the functions listed below.
3. **(C++ only)** Provide a `build.sh` script and `setup.py` similar to the one in `games/chess/`.  This allows `setup.sh` to compile the extension.
4. **Add a YAML config** under `configs/` describing how the engine should load your backend. See `configs/connect4.yaml` or `configs/chess_value.yaml` for examples.
5. **Write tests** under `tests/` to validate basic logic such as legal move generation and terminal detection.

### Required Backend Functions

A minimal backend exposes the following API:

```python
create_init_state() -> State
get_legal_moves(state: State) -> Iterable[Move]
play_move(state: State, move: Move) -> State
check_win(state: State) -> bool
check_draw(state: State) -> bool
state_to_tensor(state: State) -> np.ndarray
```

Each `State` object may be a dataclass, namedtuple or simple struct.  The engine only passes it back to these functions.

`state_to_tensor` should convert a state into a NumPy array with shape `(channels, height, width)`, ready for consumption by neural networks or simple evaluation functions.

### Optional Helpers

For convenience you may expose additional helpers (e.g. `state_from_fen` for chess).  These are not called by the engine directly but can be useful for testing or debugging.

### Building C++ Backends

If your backend is implemented in C++, create a `build.sh` that activates the virtual environment and runs `python setup.py build_ext --inplace`.  The `setup.py` should define an extension module using PyBind11.  Running `setup.sh` in the repository root will automatically build all such backends along with the MCTS core.

### Example

The Connect Four backend in `games/connect4/c4_backend.py` is a lightweight Python implementation demonstrating the required functions.  Chess provides a full-featured C++ backend under `games/chess/`.

