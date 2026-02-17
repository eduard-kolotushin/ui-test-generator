"""In-memory stub for TaskTracker API. Same interface as TaskTrackerClient.

Test cases are JSON objects with "folder" as a top-level key (and "id" after create).
"""
from __future__ import annotations

import uuid
from typing import Any


class TaskTrackerStubClient:
    """In-memory stub implementing TaskTrackerClient interface. No HTTP.
    Stores test cases as JSON objects with top-level "id" and "folder".
    """

    def __init__(self) -> None:
        # Each item: JSON object with top-level "id", "folder", and other keys
        self._store: list[dict[str, Any]] = []

    def get_test_cases(self, folder: str) -> list[dict[str, Any]]:
        """Return all test cases in the folder (copies, include id and folder)."""
        return [dict(tc) for tc in self._store if tc.get("folder") == folder]

    def _enrich(self, folder: str, payload: dict[str, Any]) -> dict[str, Any]:
        out = dict(payload)
        out.setdefault("id", f"tc-{uuid.uuid4().hex[:12]}")
        out["folder"] = folder
        return out

    def create_test_case(self, folder: str, test_case: dict[str, Any]) -> dict[str, Any]:
        """Create a test case in the folder. Returns created object with id."""
        created = self._enrich(folder, test_case)
        self._store.append(dict(created))
        return created

    def update_test_case(self, test_case_id: str, test_case: dict[str, Any]) -> dict[str, Any]:
        """Update test case by id. Returns updated object."""
        for i, tc in enumerate(self._store):
            if tc.get("id") == test_case_id:
                updated = {**tc, **test_case, "id": test_case_id, "folder": tc["folder"]}
                self._store[i] = updated
                return updated
        raise KeyError(f"Test case not found: {test_case_id}")

    def delete_test_case(self, test_case_id: str) -> None:
        """Delete test case by id."""
        for i, tc in enumerate(self._store):
            if tc.get("id") == test_case_id:
                self._store.pop(i)
                return
        raise KeyError(f"Test case not found: {test_case_id}")
