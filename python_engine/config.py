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
DEFAULT_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "smartspace07-21")

# AI API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# Pinterest API v5 Settings
PINTEREST_APP_ID = os.getenv("PINTEREST_APP_ID", "")
PINTEREST_APP_SECRET = os.getenv("PINTEREST_APP_SECRET", "")
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN", "")
PINTEREST_REFRESH_TOKEN = os.getenv("PINTEREST_REFRESH_TOKEN", "")
PINTEREST_TARGET_USERNAME = os.getenv("PINTEREST_TARGET_USERNAME", "Smart_Spaces")

# Canva Connect API & Apps SDK Settings
CANVA_CLIENT_ID = os.getenv("CANVA_CLIENT_ID", "")
CANVA_CLIENT_SECRET = os.getenv("CANVA_CLIENT_SECRET", "")
CANVA_BRAND_TEMPLATE_ID = os.getenv("CANVA_BRAND_TEMPLATE_ID", "")
CANVA_APP_ID = os.getenv("CANVA_APP_ID", "AAHOGH31K5Q")
CANVA_APP_ORIGIN = os.getenv("CANVA_APP_ORIGIN", "https://app-aahogh31k5q.canva-apps.com")

# Server & Paths
PORT = int(os.getenv("PINFORGE_PORT", "8000"))
HOST = os.getenv("PINFORGE_HOST", "0.0.0.0")
BASE_URL = os.getenv("NEXT_PUBLIC_SITE_URL", "https://pinforge.vercel.app")

STATIC_DIR = BASE_DIR / "static"
PINS_DIR = STATIC_DIR / "pins"
DATA_DIR = BASE_DIR / "data"
FONTS_DIR = BASE_DIR / "fonts"

# Ensure output directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
PINS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)

