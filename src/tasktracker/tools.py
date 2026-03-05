from __future__ import annotations

from typing import Any, Dict, List

from src.tasktracker.client import TaskTrackerClient, flatten_test_cases


def get_root_folder_units(
    space_id_code: str = "TMS",
    page: int = 0,
    size: int = 50,
) -> Dict[str, Any]:
    """
    Low-level API wrapper: get folder hierarchy from root and paginated units.
    """
    client = TaskTrackerClient.from_env()
    return client.get_root_folder_units(
        space_id_code=space_id_code,
        page=page,
        size=size,
    )


def create_folder(
    name: str,
    parent_id_code: str,
    space_id_code: str = "TMS",
) -> Dict[str, Any]:
    """
    Low-level API wrapper: create a folder under the given parent.
    """
    client = TaskTrackerClient.from_env()
    return client.create_folder(
        name=name,
        parent_id_code=parent_id_code,
        space_id_code=space_id_code,
    )


def get_test_cases(folder_code: str, page: int = 0, size: int = 50) -> List[Dict[str, Any]]:
    """
    Low-level API wrapper: fetch test cases for a given folder and flatten them.
    """
    client = TaskTrackerClient.from_env()
    raw = client.get_test_cases(folder_code=folder_code, page=page, size=size)
    return flatten_test_cases(raw)


def create_test_case(suit: str, test_case_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Low-level API wrapper: create a new test case.
    """
    client = TaskTrackerClient.from_env()
    return client.create_test_case(suit=suit, payload=test_case_json)


def update_test_case(code: str, patch_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Low-level API wrapper: update an existing test case by code.
    """
    client = TaskTrackerClient.from_env()
    return client.update_test_case(code=code, patch_body=patch_json)


def get_test_case(code: str) -> Dict[str, Any]:
    """
    Low-level API wrapper: fetch a single test case (unit) by code.
    """
    client = TaskTrackerClient.from_env()
    return client.get_test_case(code=code)

