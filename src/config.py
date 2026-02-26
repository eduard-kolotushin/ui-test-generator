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


def get_tasktracker_base_url() -> str:
    """
    Base URL for the TaskTracker API, e.g. `https://portal.works.prod.sbt/swtr`.

    Configured via `TASKTRACKER_BASE_URL`.
    """
    value = os.getenv("TASKTRACKER_BASE_URL")
    if not value:
        raise RuntimeError(
            "TASKTRACKER_BASE_URL is not set. "
            "Example: https://portal.works.prod.sbt/swtr"
        )
    return value.rstrip("/")


def get_tasktracker_token() -> Optional[str]:
    """
    Optional bearer token for authenticating with TaskTracker.

    If your deployment uses another auth mechanism (cookies, mTLS, etc.),
    adapt the client in `src/tasktracker/client.py` accordingly.
    """
    return os.getenv("TASKTRACKER_TOKEN")

