#!/usr/bin/env bash
pip install -r requirements.txt

set -euo pipefail

# ─────── Config ───────
ROOT_DIR="engine/games"
# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

# ─────── Main Loop ───────
for dir in "$ROOT_DIR"/*/; do
    game=$(basename "$dir")
    echo -n "Building ${game}… "

    if [ ! -f "${dir}build.sh" ]; then
        # no build script → auto-success
        echo -e "${GREEN}SUCCESS (no build.sh)${RESET}"
    else
        # run it silently; capture exit code
        if bash "${dir}build.sh" > /dev/null 2>&1; then
            echo -e "${GREEN}SUCCESS${RESET}"
        else
            echo -e "${RED}FAILED${RESET}"
        fi
    fi
done


pip install -e .


