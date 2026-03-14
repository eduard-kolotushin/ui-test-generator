"""
TaskTracker tools for the Deep Agent.

DEPRECATED: TaskTracker access is now via the MCP server. This module re-exports
the MCP-backed tools from src.mcp.tasktracker_client_tools for backwards
compatibility. New code should import from src.mcp.tasktracker_client_tools
directly. The agent graph (src.agent.graph) already uses the MCP client tools.
"""
from __future__ import annotations

from src.mcp.tasktracker_client_tools import (
    CreateFolderInput,
    CreateTestCaseFromStepsInput,
    CreateTestCaseInput,
    GetRootFolderUnitsInput,
    GetSingleTestCaseInput,
    GetTestCasesInput,
    UpdateTestCaseFromStepsInput,
    UpdateTestCaseInput,
    create_folder_tool,
    create_test_case_from_steps_tool,
    create_test_case_tool,
    get_root_folder_units_tool,
    get_single_test_case_tool,
    get_test_cases_tool,
    update_test_case_from_steps_tool,
    update_test_case_tool,
)

# Re-export TestStepSpec for code that builds CreateTestCaseFromStepsInput
from src.tasktracker.steps import TestStepSpec

__all__ = [
    "CreateFolderInput",
    "CreateTestCaseFromStepsInput",
    "CreateTestCaseInput",
    "GetRootFolderUnitsInput",
    "GetSingleTestCaseInput",
    "GetTestCasesInput",
    "UpdateTestCaseFromStepsInput",
    "UpdateTestCaseInput",
    "TestStepSpec",
    "create_folder_tool",
    "create_test_case_from_steps_tool",
    "create_test_case_tool",
    "get_root_folder_units_tool",
    "get_single_test_case_tool",
    "get_test_cases_tool",
    "update_test_case_from_steps_tool",
    "update_test_case_tool",
]

