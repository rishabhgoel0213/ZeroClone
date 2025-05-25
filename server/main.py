#!/usr/bin/env python3
"""
FastAPI server for interacting with the game engine.

Endpoints:
- POST /play_move: play a user move on a specific game instance
- POST /play_mcts: play a move via the MCTS bot on a specific game instance
- POST /add_game: add a new game instance and receive its index
- GET  /state/{idx}: fetch the current state of a specific game instance
"""

import argparse
import os
import collections
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from engine.engine import Engine

# === Game-agnostic state serializer ===
def serialize_state(s: object) -> dict:
    """
    Turn any backend State object into a dict of primitives/lists.
    - If it has .board, dump that (list or nested list).
    - If it has simple attrs (turn, etc), include those.
    """
    out = {}
    # 1) board
    if hasattr(s, 'board'):
        b = getattr(s, 'board')
        try:
            out['board'] = list(b)
        except Exception:
            out['board'] = b

    # 2) any other simple attributes
    for name in dir(s):
        if name.startswith('_') or name == 'board':
            continue
        try:
            v = getattr(s, name)
        except Exception:
            continue
        if isinstance(v, (int, float, str, bool)):
            out[name] = v
        elif isinstance(v, collections.deque):
            out[name] = list(v)
    return out

# Path to config; set via CLI or CONFIG_PATH env var
config_path: str = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Engine on startup
    cfg = config_path or os.getenv("CONFIG_PATH")
    if not cfg:
        raise RuntimeError(
            "Config file path must be set. Use `python api.py -c` or set CONFIG_PATH env var"
        )
    app.state.engine = Engine(cfg)
    yield
    # (Optional) add shutdown logic here

# Create app with lifespan handler
app = FastAPI(lifespan=lifespan)

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
    try:
        move = (req.move, 0)
        result = app.state.engine.play_move(move, req.idx)
        state  = app.state.engine.get_state(req.idx)
        return {"idx": req.idx, "result": result, **serialize_state(state)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/play_mcts")
def play_mcts(req: MCTSRequest):
    try:
        result = app.state.engine.play_mcts(req.idx, req.simulations, req.c)
        state  = app.state.engine.get_state(req.idx)
        return {"idx": req.idx, "result": result, **serialize_state(state)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/add_game")
def add_game():
    try:
        idx = app.state.engine.add_game()
        return {"idx": idx}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state/{idx}")
def get_state(idx: int):
    try:
        state = app.state.engine.get_state(idx)
        return {"idx": idx, **serialize_state(state)}
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

    global config_path
    config_path = args.config

    os.environ["CONFIG_PATH"] = args.config
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()




