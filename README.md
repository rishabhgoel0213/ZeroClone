# AlphaZero-Dev

A personal journey to implement and understand DeepMind's AlphaGo Zero and AlphaZero algorithms from the ground up. Starting with basic math and machine learning knowledge, this project incrementally builds up the complexity of games and techniques to achieve high-level performance.

## Project Goals

- Reproduce the results of AlphaGo Zero and AlphaZero.
- Begin with simple games and progressively tackle more complex ones.
- Implement and understand core components like Monte Carlo Tree Search (MCTS) and neural networks.
- Achieve maximum skill level possible on each game using advanced techniques.

## Repository Structure

- `VanillaMCTS/`: Basic implementation of MCTS without heuristics.
- `HeuristicMCTS/`: MCTS enhanced with heuristic evaluations.
- `ValueNetMCTS/`: Integration of a value network with MCTS.
- `.devcontainer/`: Development container configurations.
- `requirements.txt`: List of Python dependencies.

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rishabhgoel0213/alphazero-dev.git
   cd alphazero-dev
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run a specific module:**
   Navigate to the desired directory (e.g., `VanillaMCTS/`) and execute the main script:
   ```bash
   python main.py
   ```

## Progression Plan

The project follows a step-by-step approach:

1. Implement basic MCTS to understand the search algorithm.
2. Enhance MCTS with heuristics to improve decision-making.
3. Integrate a value network to evaluate game states.
4. Develop a policy network to predict optimal moves.
5. Combine MCTS with policy and value networks to replicate AlphaZero's approach.
6. Apply the framework to increasingly complex games, starting from simple ones like Tic-Tac-Toe to more complex ones like Go or Chess.

## Contributing

This is a personal learning project, but contributions are welcome. If you have suggestions or improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
