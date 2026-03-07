"""
Wrapper around the real TaskTracker client that stubs only mutating operations.

When TASKTRACKER_DRY_RUN is set, read operations (get_root_folder_units,
get_test_cases, get_test_case) go to the real API. create_folder, create_test_case,
and update_test_case return success without calling the API.
"""
from __future__ import annotations

from typing import Any, Dict, List

_DRY_RUN_CREATE_COUNTER = 0


class DryRunTaskTrackerClient:
    """
    Wraps the real client and delegates all reads to it.
    create_folder, create_test_case, update_test_case return fake success without API calls.
    """

    def __init__(self, real_client: Any) -> None:
        self._client = real_client

    def get_root_folder_units(
        self,
        *,
        space_id_code: str = "PVM",
        page: int = 0,
        size: int = 50,
    ) -> Dict[str, Any]:
        return self._client.get_root_folder_units(
            space_id_code=space_id_code,
            page=page,
            size=size,
        )

    def create_folder(
        self,
        name: str,
        parent_id_code: str,
        space_id_code: str = "PVM",
    ) -> Dict[str, Any]:
        return {
            "id": {"code": "dry-run-folder"},
            "key": "dry-run-folder",
            "title": name,
            "children": [],
        }

    def get_test_cases(
        self,
        folder_code: str,
        page: int = 0,
        size: int = 50,
    ) -> Dict[str, Any]:
        return self._client.get_test_cases(
            folder_code=folder_code,
            page=page,
            size=size,
        )

    def create_test_case(self, suit: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        global _DRY_RUN_CREATE_COUNTER
        _DRY_RUN_CREATE_COUNTER += 1
        return {"id": f"DRY-RUN-{_DRY_RUN_CREATE_COUNTER}"}

    def get_test_case(self, code: str) -> Dict[str, Any]:
        return self._client.get_test_case(code=code)

    def update_test_case(self, code: str, patch_body: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": code}
