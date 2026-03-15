"""
LangChain StructuredTools that call the TaskTracker MCP server in-process.

Used by the Deep Agent so all TaskTracker access goes through the same MCP
tool implementations (single authoritative path). The MCP server instance
is imported and call_tool() is invoked with the same argument schemas
the agent expects.
"""
from __future__ import annotations

import ast
import asyncio
import json
import logging
from typing import Any, Dict, List, Union

log = logging.getLogger(__name__)

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tasktracker.steps import TestStepSpec


def _one_step_to_dict(item: Any) -> Dict[str, Any] | None:
    """Coerce a single step to a dict with step_description, step_data, step_result."""
    if isinstance(item, dict):
        return {
            "step_description": item.get("step_description", ""),
            "step_data": item.get("step_data", ""),
            "step_result": item.get("step_result", ""),
        }
    if isinstance(item, str) and item.strip():
        try:
            parsed = json.loads(item)
        except (json.JSONDecodeError, TypeError):
            try:
                parsed = ast.literal_eval(item)
            except (ValueError, SyntaxError):
                return None
        if isinstance(parsed, dict):
            return {
                "step_description": parsed.get("step_description", ""),
                "step_data": parsed.get("step_data", ""),
                "step_result": parsed.get("step_result", ""),
            }
    return None


def _steps_from_string_or_list(v: Any) -> Any:
    """Coerce steps to a list of step dicts; LLMs sometimes pass a JSON string or Python literal."""
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
        except (json.JSONDecodeError, TypeError):
            try:
                parsed = ast.literal_eval(s)
            except (ValueError, SyntaxError):
                return v
        if isinstance(parsed, list):
            out = []
            for item in parsed:
                step_dict = _one_step_to_dict(item)
                if step_dict is not None:
                    out.append(step_dict)
            return out
    if isinstance(v, list):
        out = []
        for item in v:
            step_dict = _one_step_to_dict(item)
            if step_dict is not None:
                out.append(step_dict)
        return out
    return v


def _get_mcp():
    """Lazy import to avoid loading FastMCP and tasktracker deps at module level."""
    from src.mcp.tasktracker_server import mcp
    return mcp


def _tool_result_to_python(result: Any) -> Any:
    """Extract Python value from FastMCP ToolResult (content or structured_content)."""
    if result is None:
        return None
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "content") and result.content:
        first = result.content[0]
        if hasattr(first, "text"):
            try:
                return json.loads(first.text)
            except (json.JSONDecodeError, TypeError):
                return first.text
    return result


def _call_mcp_sync(name: str, arguments: Dict[str, Any]) -> Any:
    """Call MCP tool by name with given arguments; run async call_tool from sync context."""
    mcp = _get_mcp()

    async def _run() -> Any:
        tr = await mcp.call_tool(name, arguments)
        return _tool_result_to_python(tr)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, _run())
            return future.result()
    return asyncio.run(_run())


# --- Input schemas (same as agent/tools.py for compatibility) ---


class GetRootFolderUnitsInput(BaseModel):
    space_id_code: str = Field(
        "PVM",
        description="Space ID code for the root folder (e.g. VIEW, PVM).",
    )
    page: int = Field(0, description="Page number (0-based).", ge=0)
    size: int = Field(50, description="Page size.", ge=1, le=500)


class CreateFolderInput(BaseModel):
    name: str = Field(..., description="Name of the new folder.")
    parent_id_code: str = Field(
        ...,
        description=(
            "Code of the parent folder (e.g. TMS_test_case for root, or a child folder code)."
        ),
    )
    space_id_code: str = Field(
        "PVM",
        description="Space ID code (e.g. VIEW, PVM).",
    )


class GetTestCasesInput(BaseModel):
    folder_code: str = Field(
        ...,
        description=(
            "Code of the TaskTracker folder that contains test cases, "
            "for example `TMS_test_case` or a nested folder code."
        ),
    )
    page: int = Field(0, description="Page number to fetch (0-based).", ge=0)
    size: int = Field(50, description="Page size (number of test cases to fetch).", ge=1, le=500)


class CreateTestCaseInput(BaseModel):
    summary: str = Field(
        ...,
        description="Human-readable test case summary / title.",
    )
    suit: str = Field(
        "test_case",
        description="TaskTracker suit code for test cases (usually `test_case`).",
    )
    space: str = Field(
        ...,
        description="TaskTracker space code (e.g. `PVM`, `VIEW`).",
    )
    folder_code: str = Field(
        ...,
        description="Code of the TaskTracker folder where the new test case should be created.",
    )
    # Accept str or list so agent output is never rejected; wrapper normalizes to list[dict] for MCP.
    steps: Union[str, List[Any]] = Field(
        ...,
        description=(
            "Ordered list of test steps (or JSON string of that list). Each step has "
            "step_description, step_data (optional), step_result."
        ),
    )


class CreateTestCaseFromStepsInput(BaseModel):
    suit: str = Field(
        "test_case",
        description="TaskTracker suit code for test cases (usually `test_case`).",
    )
    test_case_base: Dict[str, Any] = Field(
        ...,
        description=(
            "Base JSON payload for the new test case (summary, attributes, etc.), "
            "WITHOUT the `attributes.test_step` field. "
            "This should typically be copied or adapted from an existing test case."
        ),
    )
    steps: Union[str, List[Any]] = Field(
        ...,
        description=(
            "Ordered list of test steps (or JSON string of that list). "
            "Each step: step_description, step_data (optional), step_result."
        ),
    )


class UpdateTestCaseInput(BaseModel):
    code: str = Field(
        ...,
        description="Code of the existing TaskTracker test case to update, e.g. `PVM-123`.",
    )
    steps: Union[str, List[Any]] = Field(
        ...,
        description=(
            "Ordered list of test steps (or JSON string of that list). "
            "Each step: step_description, step_data (optional), step_result."
        ),
    )


class GetSingleTestCaseInput(BaseModel):
    code: str = Field(
        ...,
        description="Code of the TaskTracker test case to fetch, e.g. `PVM-123`.",
    )


# --- Tool implementations that delegate to MCP ---


def _get_root_folder_units(**kwargs: Any) -> Any:
    return _call_mcp_sync("get_root_folder_units", kwargs)


def _create_folder(**kwargs: Any) -> Any:
    return _call_mcp_sync("create_folder", kwargs)


def _get_test_cases(**kwargs: Any) -> Any:
    return _call_mcp_sync("get_test_cases", kwargs)


def _get_test_case(**kwargs: Any) -> Any:
    return _call_mcp_sync("get_test_case", kwargs)


def _normalize_steps_for_mcp(steps: Any) -> List[Dict[str, Any]]:
    """Always produce a list of step dicts for MCP; run regardless of schema validation."""
    raw_list = _steps_from_string_or_list(steps)
    if not isinstance(raw_list, list):
        return []
    return [d for d in (_one_step_to_dict(item) for item in raw_list) if d is not None]


def _create_test_case(**kwargs: Any) -> Any:
    args = dict(kwargs)
    if "steps" in args:
        args["steps"] = _normalize_steps_for_mcp(args["steps"])
    log.info(
        "create_test_case (to MCP): summary=%s folder_code=%s steps_len=%s",
        args.get("summary"),
        args.get("folder_code"),
        len(args.get("steps") or []),
    )
    log.debug("create_test_case (to MCP) steps: %s", json.dumps(args.get("steps"), ensure_ascii=False)[:2000])
    return _call_mcp_sync("create_test_case", args)


def _create_test_case_from_steps(**kwargs: Any) -> Any:
    args = dict(kwargs)
    if "steps" in args:
        args["steps"] = _normalize_steps_for_mcp(args["steps"])
    log.info("create_test_case_from_steps (to MCP): steps_len=%s", len(args.get("steps") or []))
    return _call_mcp_sync("create_test_case_from_steps", args)


def _update_test_case_from_steps(**kwargs: Any) -> Any:
    args = dict(kwargs)
    if "steps" in args:
        args["steps"] = _normalize_steps_for_mcp(args["steps"])
    log.info(
        "update_test_case_from_steps (to MCP): code=%s steps_len=%s",
        args.get("code"),
        len(args.get("steps") or []),
    )
    log.debug("update_test_case_from_steps (to MCP) steps: %s", json.dumps(args.get("steps"), ensure_ascii=False)[:2000])
    return _call_mcp_sync("update_test_case_from_steps", args)


# --- LangChain StructuredTools ---


def get_root_folder_units_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="get_root_folder_units",
        description=(
            "Get the root folder hierarchy and paginated units (test cases) from the root. "
            "Use this to discover folder structure and root-level test cases."
        ),
        func=_get_root_folder_units,
        args_schema=GetRootFolderUnitsInput,
    )


def create_folder_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="create_folder",
        description=(
            "Create a new TaskTracker folder under the given parent. "
            "Use get_root_folder_units to discover parent folder codes."
        ),
        func=_create_folder,
        args_schema=CreateFolderInput,
    )


def get_test_cases_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="get_test_cases",
        description=(
            "List TaskTracker test cases in the given folder. "
            "Use this to read existing tests to use as templates for new ones."
        ),
        func=_get_test_cases,
        args_schema=GetTestCasesInput,
    )


def get_single_test_case_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="get_test_case",
        description="Fetch a single TaskTracker test case by code.",
        func=_get_test_case,
        args_schema=GetSingleTestCaseInput,
    )


def create_test_case_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="create_test_case",
        description=(
            "High-level TaskTracker test creation tool. "
            "Provide summary, suit, space, folder_code, and an ordered list of steps. "
            "The tool builds a safe base JSON from the canonical example and creates the test case."
        ),
        func=_create_test_case,
        args_schema=CreateTestCaseInput,
    )


def create_test_case_from_steps_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="create_test_case_from_steps",
        description=(
            "Create a new TaskTracker test case from a simple list of steps. "
            "You provide a base JSON payload (without `attributes.test_step`) and "
            "an ordered list of step triples: (step_description, step_data, step_result). "
            "The tool builds the nested `attributes.test_step` structure and calls "
            "the TaskTracker API."
        ),
        func=_create_test_case_from_steps,
        args_schema=CreateTestCaseFromStepsInput,
    )


def update_test_case_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="update_test_case_from_steps",
        description=(
            "Update an existing test case's steps by code. Provide the test case code and "
            "an ordered list of steps (step_description, step_data, step_result). "
            "The tool builds the correct patch body and calls the API."
        ),
        func=_update_test_case_from_steps,
        args_schema=UpdateTestCaseInput,
    )
