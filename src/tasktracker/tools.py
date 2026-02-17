"""LangChain tools for TaskTracker: get, create, update, delete test cases."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from src.tasktracker.client import get_client


@tool
def get_test_cases(folder: str) -> str:
    """Get all test cases in a given folder.
    Use this to inspect existing tests in a folder (e.g. 'postgres datasource') before generating similar ones elsewhere.
    """
    client = get_client()
    cases = client.get_test_cases(folder)
    return json.dumps(cases, indent=2, default=str)


@tool
def create_test_case(folder: str, test_case_json: str) -> str:
    """Create a new test case in the specified folder.
    test_case_json must be a valid JSON object representing the test case (structure depends on your TaskTracker schema).
    """
    try:
        payload = json.loads(test_case_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON for test case: {e}"
    if not isinstance(payload, dict):
        return "test_case_json must be a JSON object."
    client = get_client()
    created = client.create_test_case(folder, payload)
    return json.dumps(created, indent=2, default=str)


@tool
def update_test_case(test_case_id: str, test_case_json: str) -> str:
    """Update an existing test case by its ID.
    test_case_json must be a valid JSON object with the fields to update.
    """
    try:
        payload = json.loads(test_case_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON for test case: {e}"
    if not isinstance(payload, dict):
        return "test_case_json must be a JSON object."
    client = get_client()
    updated = client.update_test_case(test_case_id, payload)
    return json.dumps(updated, indent=2, default=str)


@tool
def delete_test_case(test_case_id: str) -> str:
    """Delete a test case by its ID."""
    client = get_client()
    client.delete_test_case(test_case_id)
    return f"Test case {test_case_id} deleted successfully."


def get_all_tools() -> list[Any]:
    """Return the list of TaskTracker tools for the agent."""
    return [get_test_cases, create_test_case, update_test_case, delete_test_case]
