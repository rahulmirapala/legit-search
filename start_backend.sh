#!/bin/bash
# Start the FastAPI backend with flexible interpreter resolution.
# Priority order:
# 1. Project venv at ./venv
# 2. Existing external env (previous session) at Chicken-Disease-Classification/chicken
# 3. System python

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN=""

if [[ -d "venv" && -x "venv/bin/python" ]]; then
	PYTHON_BIN="venv/bin/python"
elif [[ -x "/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python" ]]; then
	PYTHON_BIN="/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python"
else
	PYTHON_BIN="python"
fi

echo "[start_backend] Using interpreter: $PYTHON_BIN" >&2

exec "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
