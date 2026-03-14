"""
TaskTracker MCP server using FastMCP.

Exposes folder and test case operations as MCP tools so Cursor and other
MCP clients can manage TaskTracker test cases. Uses existing TaskTracker
client and config (TASKTRACKER_BASE_URL, auth, TASKTRACKER_DRY_RUN).
"""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from src.tasktracker.steps import create_test_case_from_steps as steps_create
from src.tasktracker.tools import (
    create_folder as tt_create_folder,
    create_test_case as tt_create_test_case,
    get_root_folder_units as tt_get_root_folder_units,
    get_test_case as tt_get_test_case,
    get_test_cases as tt_get_test_cases,
    update_test_case as tt_update_test_case,
)

mcp = FastMCP(
    name="tasktracker-ui-tests",
    instructions="TaskTracker tools for listing folders, test cases, and creating or updating test cases for the Grafana-based monitoring platform.",
)


def _serialize_result(value: Any) -> Any:
    """Ensure result is JSON-serializable for MCP (e.g. no custom types)."""
    if isinstance(value, (list, dict)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


@mcp.tool()
def get_root_folder_units(
    space_id_code: str = "PVM",
    page: int = 0,
    size: int = 50,
) -> dict[str, Any]:
    """
    Get the root folder hierarchy and paginated units (test cases) from the root.
    Use this to discover folder structure and root-level test cases.
    """
    result = tt_get_root_folder_units(
        space_id_code=space_id_code,
        page=page,
        size=size,
    )
    return _serialize_result(result)


@mcp.tool()
def create_folder(
    name: str,
    parent_id_code: str,
    space_id_code: str = "PVM",
) -> dict[str, Any]:
    """
    Create a new TaskTracker folder under the given parent.
    Use get_root_folder_units to discover parent folder codes.
    """
    result = tt_create_folder(
        name=name,
        parent_id_code=parent_id_code,
        space_id_code=space_id_code,
    )
    return _serialize_result(result)


@mcp.tool()
def get_test_cases(
    folder_code: str,
    page: int = 0,
    size: int = 50,
) -> list[dict[str, Any]]:
    """
    List TaskTracker test cases in the given folder.
    Use this to read existing tests to use as templates for new ones.
    """
    result = tt_get_test_cases(
        folder_code=folder_code,
        page=page,
        size=size,
    )
    return _serialize_result(result)


@mcp.tool()
def get_test_case(code: str) -> dict[str, Any]:
    """Fetch a single TaskTracker test case by code (e.g. PVM-123)."""
    result = tt_get_test_case(code=code)
    return _serialize_result(result)


@mcp.tool()
def create_test_case(suit: str, test_case_json: dict[str, Any]) -> dict[str, Any]:
    """
    Low-level test creation. test_case_json must match TaskTracker API schema.
    Prefer create_test_case_from_steps for normal usage.
    """
    result = tt_create_test_case(
        suit=suit,
        test_case_json=test_case_json,
    )
    return _serialize_result(result)


@mcp.tool()
def create_test_case_from_steps(
    suit: str,
    test_case_base: dict[str, Any],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create a new test case from a base JSON payload and an ordered list of steps.
    Each step is an object with step_description, step_data (optional), step_result.
    The tool builds the attributes.test_step structure and calls the API.
    """
    result = steps_create(
        suit=suit,
        test_case_base=test_case_base,
        steps=steps,
    )
    return _serialize_result(result)


@mcp.tool()
def update_test_case(code: str, patch_json: dict[str, Any]) -> dict[str, Any]:
    """Update an existing TaskTracker test case by code using a JSON patch body."""
    result = tt_update_test_case(
        code=code,
        patch_json=patch_json,
    )
    return _serialize_result(result)


def main() -> None:
    """Run the MCP server over stdio (for Cursor and other MCP hosts)."""
    mcp.run()


if __name__ == "__main__":
    main()
