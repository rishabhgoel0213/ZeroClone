from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple


SCRIPTS_DIR = Path(__file__).resolve().parent
TRAIN_SCRIPT = SCRIPTS_DIR / "train.py"
LOG_DIR = Path("logs")


# ──────────────────────────────────────────────────────────────────────────
#  Helper – start a background process
# ──────────────────────────────────────────────────────────────────────────
def _start_training(cmd: list[str]) -> Tuple[subprocess.Popen, Optional[Path]]:
    LOG_DIR.mkdir(exist_ok=True)
    before = set(LOG_DIR.glob("train_*.log"))

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    time.sleep(1.0)
    after = set(LOG_DIR.glob("train_*.log"))
    new_logs = sorted(after - before, key=lambda p: p.stat().st_mtime)

    return proc, (new_logs[-1] if new_logs else None)


def _parse_stats_row(row: list[str]) -> tuple[str, dict]:
    stage_idx = next((i for i, v in enumerate(row) if not v.replace(".", "", 1).isdigit()), None)
    if stage_idx is None:
        return "", {}

    stage = row[stage_idx]
    info: dict = {"stage": stage}

    try:
        if stage == "pid":
            info["pid"] = int(row[stage_idx - 1])

        elif stage == "cycle_start":
            info["cycle"]        = int(row[1])
            info["games_target"] = int(row[2])
            info["sims"]         = int(row[3])
            info["total_cycles"] = int(row[stage_idx + 1])

        elif stage == "game_done":
            info["cycle"]    = int(row[1])
            info["finished"] = int(row[2])
            info["target"]   = int(row[stage_idx + 1])

        elif stage == "train_done":
            info["cycle"]  = int(row[1])
            info["epochs"] = int(row[2])
            info["loss"]   = float(row[3])

    except (ValueError, IndexError, KeyError):
        pass
    
    return stage, info



import select, os, signal, sys, csv

def view_log(log_path: Path) -> None:
    if not log_path.exists():
        print(f"[manager] Log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    pid = None
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line or not line[0].isdigit():
                continue
            try:
                row = next(csv.reader([line]))
            except csv.Error:
                continue
            stage, info = _parse_stats_row(row)
            if stage == "pid":
                pid = info["pid"]
                break

    if not pid:
        print("[manager] ⚠️  PID not found in log; kill feature disabled.", file=sys.stderr)

    print(f"[manager] Viewing {log_path}")
    print("          type 'k' + ENTER to kill the run,  Ctrl-C to quit\n")

    current_cycle, finished, target = None, 0, 0
    with log_path.open("r", encoding="utf-8") as fh:
        fh.seek(0, os.SEEK_END)

        while True:
            rlist, _, _ = select.select([fh, sys.stdin], [], [], 0.5)

            if sys.stdin in rlist:
                cmd = sys.stdin.readline().strip().lower()
                if cmd == "k" and pid:
                    os.kill(pid, signal.SIGTERM)
                    print(f"\n[manager] Sent SIGTERM to PID {pid}")
                    break

            if fh in rlist:
                line = fh.readline()
                if not line:
                    continue
                if not line[0].isdigit():
                    continue
                try:
                    row = next(csv.reader([line]))
                except csv.Error:
                    continue

                stage, info = _parse_stats_row(row)
                if not stage:
                    continue

                if stage == "cycle_start":
                    current_cycle = info["cycle"]
                    target        = info["games_target"]
                    finished      = 0
                    print(f"\n▶ Cycle {current_cycle}  –  target {target} games")

                elif stage == "game_done":
                    if current_cycle is None:
                        current_cycle = info["cycle"]
                        target        = info["target"]
                        finished      = 0
                        print(f"\n▶ Cycle {current_cycle}   target {target} games")

                    if info["cycle"] != current_cycle:
                        continue

                    finished = info["finished"]
                    target   = info["target"]
                    pct      = 100.0 * finished / max(1, target)
                    print(f"\r   progress: {finished}/{target}  ({pct:.1f}% )", end="", flush=True)

                elif stage == "train_done":
                    print("\n\n🎉  Training run complete!\n")
                    break

# ──────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="ZeroClone training manager")
    ap.add_argument("-c", "--config", help="YAML config to pass to train.py when *starting* a run")
    ap.add_argument("--view", action="store_true", help="Follow an existing run instead of starting a new one")
    ap.add_argument("-l", "--log-file", type=Path, help="Explicit log file to view (defaults to newest)")
    ap.add_argument("remainder", nargs=argparse.REMAINDER, help="Extra flags after '--' are forwarded to train.py")
    args = ap.parse_args()

    if args.view:
        log_path = (
            args.log_file
            if args.log_file
            else max(LOG_DIR.glob("train_*.log"), key=lambda p: p.stat().st_mtime)
        )
        view_log(log_path)
        return

    if not args.config:
        print("Must supply -c/--config when starting a run", file=sys.stderr)
        sys.exit(1)

    cmd = ["python", str(TRAIN_SCRIPT), "-c", args.config] + args.remainder
    proc, log_path = _start_training(cmd)

    print(f"[manager] Started training – PID {proc.pid}")
    if log_path:
        print(f"[manager] Logfile      – {log_path}")
        print(f"[manager] View live     – python scripts/train_manager.py --view -l {log_path}")
    else:
        print("[manager] Logfile not detected yet (check ./logs/ manually)")


if __name__ == "__main__":
    main()
