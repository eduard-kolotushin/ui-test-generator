"""Configuration loaded from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def get_tasktracker_base_url() -> str:
    return os.getenv("TASKTRACKER_BASE_URL", "http://localhost:8000/api")


def get_tasktracker_api_key() -> str | None:
    return os.getenv("TASKTRACKER_API_KEY")


def get_tasktracker_use_stub() -> bool:
    """Use in-memory stub instead of real TaskTracker API (e.g. TASKTRACKER_USE_STUB=true)."""
    return os.getenv("TASKTRACKER_USE_STUB", "").lower() in ("1", "true", "yes")


def get_gigachat_credentials() -> str | None:
    """GigaChat API key / auth token from env (GIGACHAT_API_KEY or GIGACHAT_CREDENTIALS)."""
    return os.getenv("GIGACHAT_API_KEY") or os.getenv("GIGACHAT_CREDENTIALS")


def get_gigachat_verify_ssl() -> bool:
    """Whether to verify SSL for GigaChat (default False for compatibility)."""
    return os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() in ("1", "true", "yes")
