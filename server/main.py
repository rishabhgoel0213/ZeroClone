#!/usr/bin/env python3
"""
FastAPI server for interacting with the game engine.

Endpoints:
- POST /play_move: play a user move on a specific game instance
- POST /play_mcts: play a move via the MCTS bot on a specific game instance
- POST /add_game: add a new game instance and receive its index
- GET  /state/{idx}: fetch the current state of a specific game instance

Usage:
    python api.py -c path/to/config.yaml [--host HOST] [--port PORT] [--reload]

The server will be available at http://HOST:PORT
"""
import argparse
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from engine.engine import Engine

app = FastAPI()
engine: Engine  # Will be initialized in main()

# Pydantic models for request bodies
class MoveRequest(BaseModel):
    idx: int = 0
    move: Any

class MCTSRequest(BaseModel):
    idx: int = 0
    simulations: int = 1000
    c: float = 1.4

@app.post("/play_move")
def play_move(req: MoveRequest):
    """Play a user-specified move on game instance `idx`."""
    try:
        result = engine.play_move(req.move, req.idx)
        state = engine.get_state(req.idx)
        return {"idx": req.idx, "result": result, "state": repr(state)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/play_mcts")
def play_mcts(req: MCTSRequest):
    """Play a move via the MCTS bot on game instance `idx`."""
    try:
        result = engine.play_mcts(req.idx, req.simulations, req.c)
        state = engine.get_state(req.idx)
        return {"idx": req.idx, "result": result, "state": repr(state)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/add_game")
def add_game():
    """Add a new game instance and get its index."""
    try:
        idx = engine.add_game()
        return {"idx": idx}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state/{idx}")
def get_state(idx: int):
    """Retrieve the current state of game instance `idx`."""
    try:
        state = engine.get_state(idx)
        return {"idx": idx, "state": repr(state)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def main():
    parser = argparse.ArgumentParser(description="FastAPI server for game engine")
    parser.add_argument(
        "-c", "--config", required=True, help="Path to game configuration YAML file"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to listen on"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload (development only)"
    )
    args = parser.parse_args()

    global engine
    engine = Engine(args.config)

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
