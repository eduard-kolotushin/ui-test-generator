"""
TaskTracker MCP server using FastMCP.

Exposes folder and test case operations as MCP tools so Cursor and other
MCP clients can manage TaskTracker test cases. Uses existing TaskTracker
client and config (TASKTRACKER_BASE_URL, auth, TASKTRACKER_DRY_RUN).
"""
from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

log = logging.getLogger(__name__)

from src.tasktracker.steps import (
    TestStepSpec,
    create_test_case_with_summary,
    update_test_case_from_steps as steps_update_from_steps,
)
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


def _step_item_to_dict(s: Any) -> dict[str, Any]:
    """Coerce a step item (dict or model) to a plain dict for TestStepSpec."""
    if isinstance(s, dict):
        return s
    if hasattr(s, "model_dump"):
        return s.model_dump()
    return {"step_description": getattr(s, "step_description", "") or "", "step_data": getattr(s, "step_data", "") or "", "step_result": getattr(s, "step_result", "") or ""}


@mcp.tool()
def create_test_case(
    summary: str,
    suit: str,
    space: str,
    folder_code: str,
) -> dict[str, Any]:
    """
    Create an empty test case in the given folder.

    TaskTracker does not accept new test cases with step codes created client-side,
    so this tool creates a test case with an empty step list. Use
    update_test_case_from_steps with the returned code to add steps afterwards.

    - `summary`: human-readable test case title.
    - `suit`: TaskTracker suit code (usually `test_case`).
    - `space`: TaskTracker space code (e.g. `PVM`, `VIEW`).
    - `folder_code`: TaskTracker folder identifier to place the test in.
    """
    log.info(
        "create_test_case tool: summary=%s folder_code=%s (empty steps)",
        summary,
        folder_code,
    )
    result = create_test_case_with_summary(
        summary=summary,
        suit=suit,
        space=space,
        folder_code=folder_code,
        steps=[],
    )
    return _serialize_result(result)


@mcp.tool()
def update_test_case_from_steps(code: str, steps: list[Any]) -> dict[str, Any]:
    """
    Update an existing test case's steps by code.

    This tool:
    - Fetches the current test case to preserve existing step codes.
    - Builds the appropriate `attributes.test_step.testStepList` patch body.
    - Calls the TaskTracker update API.
    """
    steps_dicts = [_step_item_to_dict(s) for s in (steps or [])]
    log.info(
        "update_test_case_from_steps tool: code=%s incoming_steps_len=%s steps_dicts_len=%s",
        code,
        len(steps or []),
        len(steps_dicts),
    )
    step_specs: list[TestStepSpec] = [
        TestStepSpec(
            step_description=d.get("step_description", ""),
            step_data=d.get("step_data", ""),
            step_result=d.get("step_result", ""),
        )
        for d in steps_dicts
    ]
    log.debug("update_test_case_from_steps step_specs: %s", [(s.step_description[:50], s.step_result[:50]) for s in step_specs])
    result = steps_update_from_steps(code=code, steps=step_specs)
    return _serialize_result(result)


def main() -> None:
    """Run the MCP server over stdio (for Cursor and other MCP hosts)."""
    mcp.run()


if __name__ == "__main__":
    main()
