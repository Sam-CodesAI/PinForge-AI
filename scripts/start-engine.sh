#!/usr/bin/env bash
set -e

# PinForge AI — Python Core Engine Launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Launching PinForge AI Python FastAPI Core Engine..."
cd "$WORKSPACE_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    uv venv .venv
    uv pip install --python .venv/bin/python -r python_engine/requirements.txt google-antigravity
fi

echo "Starting Uvicorn on 0.0.0.0:8000..."
cd python_engine
exec ../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload

