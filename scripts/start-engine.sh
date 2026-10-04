#!/usr/bin/env bash
set -e

# PinForge AI — Python Core Engine Launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Launching PinForge AI Python FastAPI Core Engine..."
cd "$WORKSPACE_DIR"

if [ ! -d "python_engine/.venv" ]; then
    echo "Creating virtual environment in python_engine/.venv..."
    /home/codespace/.local/bin/uv venv python_engine/.venv --python 3.14
    /home/codespace/.local/bin/uv pip install --python python_engine/.venv \
      fastapi "uvicorn[standard]" pydantic pillow curl_cffi beautifulsoup4 httpx groq google-genai apscheduler python-dotenv python-multipart
fi

echo "Starting Uvicorn on 0.0.0.0:8000 (reload enabled)..."
exec python_engine/.venv/bin/uvicorn python_engine.main:app --host 0.0.0.0 --port 8000 --reload
