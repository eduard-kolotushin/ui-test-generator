import os
from typing import Optional


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


def get_gigachat_credentials() -> str:
    """
    Return the credentials/token for GigaChat.

    Expected to be provided via the `GIGACHAT_API_KEY` environment variable.
    """
    value = os.getenv("GIGACHAT_API_KEY")
    if not value:
        raise RuntimeError(
            "GIGACHAT_API_KEY is not set. Please export your GigaChat token."
        )
    return value


def get_gigachat_verify_ssl() -> bool:
    """
    Control SSL certificate verification for GigaChat.

    Uses the `GIGACHAT_VERIFY_SSL` env var (true/false). Defaults to False to
    match common internal deployments, but you should set it to true in production
    if certificates are valid.
    """
    return _get_bool_env("GIGACHAT_VERIFY_SSL", default=False)


def get_tasktracker_use_stub() -> bool:
    """
    Whether to use the local TaskTracker stub instead of the real API.

    Set `TASKTRACKER_USE_STUB=true` for local testing. When true,
    `get_tasktracker_base_url()` defaults to the stub URL if
    TASKTRACKER_BASE_URL is not set.
    """
    return _get_bool_env("TASKTRACKER_USE_STUB", default=False)


def get_tasktracker_base_url() -> str:
    """
    Base URL for the TaskTracker API, e.g. `https://portal.works.prod.sbt/swtr`.

    When `TASKTRACKER_USE_STUB=true`, always returns the local stub URL
    (http://127.0.0.1:8765) so the app never tries to reach a private domain.
    Otherwise uses `TASKTRACKER_BASE_URL` (required).
    """
    if get_tasktracker_use_stub():
        return "http://127.0.0.1:8765"
    value = os.getenv("TASKTRACKER_BASE_URL")
    if not value:
        raise RuntimeError(
            "TASKTRACKER_BASE_URL is not set. "
            "Example: https://portal.works.prod.sbt/swtr "
            "For local testing set TASKTRACKER_USE_STUB=true and run: "
            "uv run python -m src.tasktracker.stub"
        )
    return value.rstrip("/")


def get_tasktracker_token() -> Optional[str]:
    """
    Optional bearer token for authenticating with TaskTracker.

    If your deployment uses another auth mechanism (cookies, mTLS, etc.),
    adapt the client in `src/tasktracker/client.py` accordingly.
    """
    return os.getenv("TASKTRACKER_TOKEN")

