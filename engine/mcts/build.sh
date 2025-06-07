#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source /opt/venv/bin/activate 2>/dev/null || true
python3 setup.py build_ext --inplace
