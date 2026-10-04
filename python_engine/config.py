"""PinForge AI — Engine Configuration.

Loads environment variables, default affiliate credentials, and local directories.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load workspace .env.local and .env
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent

load_dotenv(WORKSPACE_DIR / ".env.local")
load_dotenv(WORKSPACE_DIR / ".env")

# Amazon Associate Settings
DEFAULT_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "samarth0b-20")

# AI API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Server & Paths
PORT = int(os.getenv("PINFORGE_PORT", "8000"))
HOST = os.getenv("PINFORGE_HOST", "0.0.0.0")
BASE_URL = os.getenv("NEXT_PUBLIC_SITE_URL", "https://sam-codes.vercel.app")

STATIC_DIR = BASE_DIR / "static"
PINS_DIR = STATIC_DIR / "pins"
FONTS_DIR = BASE_DIR / "fonts"

# Ensure output directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
PINS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)
