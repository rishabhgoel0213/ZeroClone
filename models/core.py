"""
Global helpers for loading value-net modules and enumerating checkpoints.
"""

from pathlib import Path
from typing import List, Tuple
import importlib


def get_value_network(model_type: str) -> Tuple[object, Path]:
    module = importlib.import_module(f"models.{model_type}.network")
    latest_path = Path(__file__).resolve().parent / model_type / "latest.pth"
    return module, latest_path


def list_checkpoints(model_type: str) -> List[Path]:
    cdir = Path(__file__).resolve().parent / model_type / "checkpoints"
    if not cdir.exists():
        return []
    return sorted(cdir.glob("*.pth"))
