from __future__ import annotations

import os
from typing import Any, Dict, List

from src.tasktracker.client import TaskTrackerClient, flatten_test_cases
from src.tasktracker.dry_run_client import DryRunTaskTrackerClient


def _get_client() -> Any:
    """Return client; when TASKTRACKER_DRY_RUN is set, mutating calls are stubbed (reads go to real API)."""
    real = TaskTrackerClient.from_env()
    if os.getenv("TASKTRACKER_DRY_RUN", "").strip().lower() in ("1", "true", "yes"):
        return DryRunTaskTrackerClient(real)
    return real


def get_root_folder_units(
    space_id_code: str = "PVM",
    page: int = 0,
    size: int = 50,
) -> Dict[str, Any]:
    """
    Low-level API wrapper: get folder hierarchy from root and paginated units.
    """
    client = _get_client()
    return client.get_root_folder_units(
        space_id_code=space_id_code,
        page=page,
        size=size,
    )


def create_folder(
    name: str,
    parent_id_code: str,
    space_id_code: str = "PVM",
) -> Dict[str, Any]:
    """
    Low-level API wrapper: create a folder under the given parent.
    """
    client = _get_client()
    return client.create_folder(
        name=name,
        parent_id_code=parent_id_code,
        space_id_code=space_id_code,
    )


def get_test_cases(folder_code: str, page: int = 0, size: int = 50) -> List[Dict[str, Any]]:
    """
    Low-level API wrapper: fetch test cases for a given folder and flatten them.
    """
    client = _get_client()
    raw = client.get_test_cases(folder_code=folder_code, page=page, size=size)
    return flatten_test_cases(raw)


def create_test_case(suit: str, test_case_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Low-level API wrapper: create a new test case.
    """
    client = _get_client()
    return client.create_test_case(suit=suit, payload=test_case_json)


def update_test_case(code: str, patch_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Low-level API wrapper: update an existing test case by code.
    """
    client = _get_client()
    return client.update_test_case(code=code, patch_body=patch_json)


def get_test_case(code: str) -> Dict[str, Any]:
    """
    Low-level API wrapper: fetch a single test case (unit) by code.
    """
    client = _get_client()
    return client.get_test_case(code=code)

