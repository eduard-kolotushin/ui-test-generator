"""HTTP client for TaskTracker API. Manages test cases (CRUD) by folder.

Test cases are JSON objects with "folder" as a top-level key.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from src.config import get_tasktracker_api_key, get_tasktracker_base_url, get_tasktracker_use_stub

from src.tasktracker.stub import TaskTrackerStubClient


class TaskTrackerClient:
    """Client for TaskTracker API. Assumes REST endpoints for test cases."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or get_tasktracker_base_url()).rstrip("/")
        self.api_key = api_key or get_tasktracker_api_key()
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_test_cases(self, folder: str) -> list[dict[str, Any]]:
        """Fetch all test cases in a folder. Returns list of test case JSON objects."""
        # Assume endpoint: GET /test-cases?folder=<folder> or GET /folders/<folder>/test-cases
        url = f"{self.base_url}/test-cases"
        params = {"folder": folder}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, params=params, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        # Support both { "items": [...] } and direct list
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        if isinstance(data, dict) and "test_cases" in data:
            return data["test_cases"]
        return []

    def create_test_case(self, folder: str, test_case: dict[str, Any]) -> dict[str, Any]:
        """Create a test case in the given folder. Returns created test case JSON (folder is top-level)."""
        url = f"{self.base_url}/test-cases"
        body = {**test_case, "folder": folder}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=body, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    def update_test_case(self, test_case_id: str, test_case: dict[str, Any]) -> dict[str, Any]:
        """Update an existing test case by ID. Returns updated test case JSON."""
        url = f"{self.base_url}/test-cases/{test_case_id}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.put(url, json=test_case, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    def delete_test_case(self, test_case_id: str) -> None:
        """Delete a test case by ID."""
        url = f"{self.base_url}/test-cases/{test_case_id}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.delete(url, headers=self._headers())
            resp.raise_for_status()


# Singleton used by tools (can be overridden for testing)
_default_client: TaskTrackerClient | TaskTrackerStubClient | None = None


def get_client() -> TaskTrackerClient | TaskTrackerStubClient:
    """Return the TaskTracker client: stub if TASKTRACKER_USE_STUB is set, else real API client."""
    global _default_client
    if _default_client is None:
        if get_tasktracker_use_stub():
            _default_client = TaskTrackerStubClient()
        else:
            _default_client = TaskTrackerClient()
    return _default_client


def set_client(client: TaskTrackerClient | TaskTrackerStubClient | None) -> None:
    global _default_client
    _default_client = client
