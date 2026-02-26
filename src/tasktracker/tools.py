from __future__ import annotations

from typing import Any, Dict, List

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tasktracker.client import TaskTrackerClient, flatten_test_cases


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


def _get_test_cases_impl(folder_code: str, page: int = 0, size: int = 50) -> List[Dict[str, Any]]:
    client = TaskTrackerClient.from_env()
    raw = client.get_test_cases(folder_code=folder_code, page=page, size=size)
    return flatten_test_cases(raw)


def get_test_cases_tool() -> StructuredTool:
    """
    Deep Agents / LangChain tool for listing test cases in a folder.
    """
    return StructuredTool.from_function(
        name="get_test_cases",
        description=(
            "List TaskTracker test cases in the given folder. "
            "Use this to read existing tests to use as templates for new ones."
        ),
        func=_get_test_cases_impl,
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


def _create_test_case_impl(suit: str, test_case_json: Dict[str, Any]) -> Dict[str, Any]:
    client = TaskTrackerClient.from_env()
    return client.create_test_case(suit=suit, payload=test_case_json)


def create_test_case_tool() -> StructuredTool:
    """
    Deep Agents / LangChain tool for creating a new test case.
    """
    return StructuredTool.from_function(
        name="create_test_case",
        description=(
            "Create a new TaskTracker test case using the provided JSON payload. "
            "You must supply all required attributes according to the TaskTracker schema."
        ),
        func=_create_test_case_impl,
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


def _update_test_case_impl(code: str, patch_json: Dict[str, Any]) -> Dict[str, Any]:
    client = TaskTrackerClient.from_env()
    return client.update_test_case(code=code, patch_body=patch_json)


def update_test_case_tool() -> StructuredTool:
    """
    Deep Agents / LangChain tool for updating an existing test case.
    """
    return StructuredTool.from_function(
        name="update_test_case",
        description="Update an existing TaskTracker test case by code using a JSON patch body.",
        func=_update_test_case_impl,
        args_schema=UpdateTestCaseInput,
    )


class GetSingleTestCaseInput(BaseModel):
    code: str = Field(
        ...,
        description="Code of the TaskTracker test case to fetch, e.g. `TMS-123`.",
    )


def _get_single_test_case_impl(code: str) -> Dict[str, Any]:
    client = TaskTrackerClient.from_env()
    return client.get_test_case(code=code)


def get_single_test_case_tool() -> StructuredTool:
    """
    Helper tool: fetch a single test case by code.
    """
    return StructuredTool.from_function(
        name="get_test_case",
        description="Fetch a single TaskTracker test case by code.",
        func=_get_single_test_case_impl,
        args_schema=GetSingleTestCaseInput,
    )

