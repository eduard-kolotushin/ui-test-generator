from __future__ import annotations

from typing import Any, Dict, List

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
        "TMS",
        description="Space ID code for the root folder (e.g. TMS).",
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
        "TMS",
        description="Space ID code (e.g. TMS).",
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
    """Deep Agents / LangChain tool for creating a new test case."""
    return StructuredTool.from_function(
        name="create_test_case",
        description=(
            "Create a new TaskTracker test case using the provided JSON payload. "
            "You must supply all required attributes according to the TaskTracker schema."
        ),
        func=create_test_case,
        args_schema=CreateTestCaseInput,
    )


class UpdateTestCaseInput(BaseModel):
    code: str = Field(
        ...,
        description="Code of the existing TaskTracker test case to update, e.g. `TMS-123`.",
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
        description="Code of the TaskTracker test case to fetch, e.g. `TMS-123`.",
    )


def get_single_test_case_tool() -> StructuredTool:
    """Helper tool: fetch a single test case by code."""
    return StructuredTool.from_function(
        name="get_test_case",
        description="Fetch a single TaskTracker test case by code.",
        func=get_test_case,
        args_schema=GetSingleTestCaseInput,
    )

