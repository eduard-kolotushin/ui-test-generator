from __future__ import annotations

from typing import Any, Dict, List

import json
from copy import deepcopy
from uuid import uuid4

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tasktracker.tools import (
    create_folder,
    create_test_case,
    get_root_folder_units,
    get_test_case,
    get_test_cases,
    update_test_case,
)


# --- Folder tools ---


class GetRootFolderUnitsInput(BaseModel):
    space_id_code: str = Field(
        "PVM",
        description="Space ID code for the root folder (e.g. VIEW, PVM).",
    )
    page: int = Field(0, description="Page number (0-based).", ge=0)
    size: int = Field(50, description="Page size.", ge=1, le=500)


def get_root_folder_units_tool() -> StructuredTool:
    """List root folder hierarchy and units (test cases at root level)."""
    return StructuredTool.from_function(
        name="get_root_folder_units",
        description=(
            "Get the root folder hierarchy and paginated units (test cases) from the root. "
            "Use this to discover folder structure and root-level test cases."
        ),
        func=get_root_folder_units,
        args_schema=GetRootFolderUnitsInput,
    )


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


def create_folder_tool() -> StructuredTool:
    """Create a new folder under the given parent."""
    return StructuredTool.from_function(
        name="create_folder",
        description=(
            "Create a new TaskTracker folder under the given parent. "
            "Use get_root_folder_units to discover parent folder codes."
        ),
        func=create_folder,
        args_schema=CreateFolderInput,
    )


# --- Test case tools ---


class GetTestCasesInput(BaseModel):
    folder_code: str = Field(
        ...,
        description=(
            "Code of the TaskTracker folder that contains test cases, "
            "for example `TMS_test_case` or a nested folder code."
        ),
    )
    page: int = Field(
        0,
        description="Page number to fetch (0-based).",
        ge=0,
    )
    size: int = Field(
        50,
        description="Page size (number of test cases to fetch).",
        ge=1,
        le=500,
    )


def get_test_cases_tool() -> StructuredTool:
    """Deep Agents / LangChain tool for listing test cases in a folder."""
    return StructuredTool.from_function(
        name="get_test_cases",
        description=(
            "List TaskTracker test cases in the given folder. "
            "Use this to read existing tests to use as templates for new ones."
        ),
        func=get_test_cases,
        args_schema=GetTestCasesInput,
    )


class CreateTestCaseInput(BaseModel):
    suit: str = Field(
        "test_case",
        description="TaskTracker suit code for test cases (usually `test_case`).",
    )
    test_case_json: Dict[str, Any] = Field(
        ...,
        description=(
            "Raw JSON payload for the new test case, matching TaskTracker's API schema. "
            "The agent should base this on existing test cases from `get_test_cases`."
        ),
    )


def create_test_case_tool() -> StructuredTool:
    """Low-level tool: create a new test case from a full JSON body."""
    return StructuredTool.from_function(
        name="create_test_case",
        description=(
            "Low-level TaskTracker test creation tool. "
            "Takes a full `test_case_json` payload that already matches the API schema. "
            "Prefer `create_test_case_from_steps` for normal usage."
        ),
        func=create_test_case,
        args_schema=CreateTestCaseInput,
    )


class TestStepSpec(BaseModel):
    """
    High-level representation of a single test step.

    The tool will convert these fields into the nested `attributes.test_step`
    structure expected by TaskTracker (with formattedText JSON, step numbers, etc.).
    """

    step_description: str = Field(
        ...,
        description="Human-readable description of the step (what the user does).",
    )
    step_data: str = Field(
        "",
        description="Optional data / input used in this step (can be empty string).",
    )
    step_result: str = Field(
        ...,
        description="Expected result / assertion for this step.",
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
    steps: List[TestStepSpec] = Field(
        ...,
        description=(
            "Ordered list of test steps. Each item corresponds to one step and "
            "contains: (step_description, step_data, step_result)."
        ),
    )


def _build_formatted_text(text: str) -> str:
    """
    Wrap plain text into a minimal ProseMirror-like JSON document and dump as string.
    """
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }
    return json.dumps(doc, ensure_ascii=False)


def _build_test_steps(steps: List[TestStepSpec]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps, start=1):
        result.append(
            {
                "code": str(uuid4()),
                "stepDescription": {
                    "text": _build_formatted_text(step.step_description),
                },
                "stepData": {
                    "text": _build_formatted_text(step.step_data or ""),
                },
                "stepResult": {
                    "text": _build_formatted_text(step.step_result),
                },
                "callToTestId": None,
                "stepNumber": idx,
                "stepType": "step_by_step",
                "files": None,
            }
        )
    return result


def create_test_case_from_steps(
    suit: str,
    test_case_base: Dict[str, Any],
    steps: List[TestStepSpec],
) -> Dict[str, Any]:
    """
    High-level helper: create a new test case from a list of steps.

    Instead of asking the LLM to construct the entire nested `attributes.test_step`
    structure, this tool accepts a simple ordered list of steps (description, data,
    result) and builds a valid TaskTracker payload before calling the API.
    """
    payload = deepcopy(test_case_base)
    attributes = payload.setdefault("attributes", {})
    attributes["test_step"] = _build_test_steps(steps)
    return create_test_case(suit=suit, test_case_json=payload)


def create_test_case_from_steps_tool() -> StructuredTool:
    """
    Preferred high-level tool for creating a new TaskTracker test case.

    Provide a `test_case_base` (copied/adapted from an existing test) and a list
    of steps in the form [(step_description, step_data, step_result), ...]. The
    tool will construct the correct `attributes.test_step` structure for you.
    """
    return StructuredTool.from_function(
        name="create_test_case_from_steps",
        description=(
            "Create a new TaskTracker test case from a simple list of steps. "
            "You provide a base JSON payload (without `attributes.test_step`) and "
            "an ordered list of step triples: (step_description, step_data, step_result). "
            "The tool builds the nested `attributes.test_step` structure and calls "
            "the TaskTracker API."
        ),
        func=create_test_case_from_steps,
        args_schema=CreateTestCaseFromStepsInput,
    )


class UpdateTestCaseInput(BaseModel):
    code: str = Field(
        ...,
        description="Code of the existing TaskTracker test case to update, e.g. `PVM-123`.",
    )
    patch_json: Dict[str, Any] = Field(
        ...,
        description=(
            "Partial JSON payload for the update request, matching the TaskTracker "
            "update schema (fields to change only)."
        ),
    )


def update_test_case_tool() -> StructuredTool:
    """Deep Agents / LangChain tool for updating an existing test case."""
    return StructuredTool.from_function(
        name="update_test_case",
        description=(
            "Update an existing TaskTracker test case by code using a JSON patch body."
        ),
        func=update_test_case,
        args_schema=UpdateTestCaseInput,
    )


class GetSingleTestCaseInput(BaseModel):
    code: str = Field(
        ...,
        description="Code of the TaskTracker test case to fetch, e.g. `PVM-123`.",
    )


def get_single_test_case_tool() -> StructuredTool:
    """Helper tool: fetch a single test case by code."""
    return StructuredTool.from_function(
        name="get_test_case",
        description="Fetch a single TaskTracker test case by code.",
        func=get_test_case,
        args_schema=GetSingleTestCaseInput,
    )

