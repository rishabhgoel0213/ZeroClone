# Guidelines for Codex Agent

## Environment Setup
The repository expects a Python 3 environment with build tools. The agent can
reproduce the Docker image in this container without actually running Docker:

1. Install OS packages (if not already present):
   ```bash
   apt-get update && \
   apt-get install -y --no-install-recommends \
       python3 python3-venv python3-pip python3-dev \
       build-essential git openssh-client wget ca-certificates
   ```
2. Create and activate a virtual environment under `/opt/venv`:
   ```bash
   python3 -m venv /opt/venv
   source /opt/venv/bin/activate
   pip install --upgrade pip
   ```
3. Install Python dependencies. No GPU is available, so the CPU
   version of PyTorch from PyPI is sufficient:
   ```bash
   pip install -r requirements.txt
   ```
4. Build the C++ extensions for each game and the MCTS backend:
   ```bash
   engine/games/chess/build.sh
   engine/mcts/build.sh
   ```
   (Other games currently have no build script.)
5. Install the project in editable mode:
   ```bash
   pip install -e .
   ```

## Running Tests
Execute all tests from the repository root after the above setup:
```bash
pytest -q
```
The test suite compiles the chess backend on the fly.

## General PR Expectations
- Ensure the repository still installs and tests pass after your changes.
- Keep commits focused and the working tree clean.
