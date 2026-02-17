"""Unit tests for TaskTracker tools using the local stub."""
import json

import pytest

from src.tasktracker.client import get_client
from src.tasktracker.tools import (
    create_test_case,
    delete_test_case,
    get_test_cases,
    update_test_case,
)


def test_get_test_cases_empty():
    result = get_test_cases.invoke({"folder": "postgres datasource"})
    assert result == "[]"


def test_create_and_get_test_cases():
    create_test_case.invoke({
        "folder": "postgres datasource",
        "test_case_json": json.dumps({"name": "Check dashboard", "steps": [{"action": "open"}]}),
    })
    result = get_test_cases.invoke({"folder": "postgres datasource"})
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["name"] == "Check dashboard"
    assert data[0]["steps"] == [{"action": "open"}]
    assert "id" in data[0]


def test_create_test_case_returns_created_with_id():
    result = create_test_case.invoke({
        "folder": "abyss",
        "test_case_json": json.dumps({"title": "Test query"}),
    })
    created = json.loads(result)
    assert created["title"] == "Test query"
    assert "id" in created
    assert created["folder"] == "abyss"


def test_update_test_case():
    create_test_case.invoke({
        "folder": "f",
        "test_case_json": json.dumps({"name": "Original"}),
    })
    listed = json.loads(get_test_cases.invoke({"folder": "f"}))
    tc_id = listed[0]["id"]
    update_test_case.invoke({
        "test_case_id": tc_id,
        "test_case_json": json.dumps({"name": "Updated"}),
    })
    listed2 = json.loads(get_test_cases.invoke({"folder": "f"}))
    assert listed2[0]["name"] == "Updated"
    assert listed2[0]["id"] == tc_id


def test_delete_test_case():
    create_test_case.invoke({
        "folder": "f",
        "test_case_json": json.dumps({"name": "To delete"}),
    })
    listed = json.loads(get_test_cases.invoke({"folder": "f"}))
    tc_id = listed[0]["id"]
    delete_test_case.invoke({"test_case_id": tc_id})
    result = get_test_cases.invoke({"folder": "f"})
    assert result == "[]"


def test_create_invalid_json_returns_error():
    result = create_test_case.invoke({
        "folder": "f",
        "test_case_json": "not json",
    })
    assert "Invalid JSON" in result


def test_stub_isolation_per_test(tasktracker_stub):
    """Each test gets a fresh stub (conftest autouse)."""
    assert get_client() is tasktracker_stub
    create_test_case.invoke({"folder": "only-here", "test_case_json": "{}"})
    data = json.loads(get_test_cases.invoke({"folder": "only-here"}))
    assert len(data) == 1
