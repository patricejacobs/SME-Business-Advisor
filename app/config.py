"""Environment configuration. Fails loudly at import if required vars are missing."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


def _path(name: str, default: str) -> Path:
    raw = os.getenv(name, default)
    p = Path(raw)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p


# Anthropic
ANTHROPIC_API_KEY = _required("ANTHROPIC_API_KEY")
MODEL = "claude-opus-4-8"

# Meta WhatsApp Cloud API
WHATSAPP_PHONE_NUMBER_ID = _required("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = _required("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_VERIFY_TOKEN = _required("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "").strip()
GRAPH_API_VERSION = "v21.0"

# Storage
DB_PATH = _path("DB_PATH", "data/agent.db")
LOG_DIR = _path("LOG_DIR", "data/logs")

# Behaviour
ALLOW_UNSIGNED_WEBHOOKS = os.getenv("ALLOW_UNSIGNED_WEBHOOKS", "0") == "1"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
