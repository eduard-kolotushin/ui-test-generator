"""
Shared high-level helpers for building TaskTracker test case steps.

Used by both the agent (LangChain tools) and the MCP server so step structure
and ProseMirror formatting stay in one place.
"""
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict, List, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from src.tasktracker.tools import create_test_case, update_test_case


class TestStepSpec(BaseModel):
    """
    High-level representation of a single test step.

    Converted into the nested `attributes.test_step` structure expected by
    TaskTracker (with formattedText JSON, step numbers, etc.).
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


def build_formatted_text(text: str) -> str:
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


def build_test_steps(steps: List[Union[TestStepSpec, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Build the TaskTracker `attributes.test_step` list from step specs.

    Accepts either TestStepSpec instances or dicts with keys step_description,
    step_data (optional), step_result.
    """
    result: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps, start=1):
        if isinstance(step, dict):
            spec = TestStepSpec(
                step_description=step.get("step_description", ""),
                step_data=step.get("step_data", ""),
                step_result=step.get("step_result", ""),
            )
        else:
            spec = step
        result.append(
            {
                "code": str(uuid4()),
                "stepDescription": {
                    "text": build_formatted_text(spec.step_description),
                },
                "stepData": {
                    "text": build_formatted_text(spec.step_data or ""),
                },
                "stepResult": {
                    "text": build_formatted_text(spec.step_result),
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
    steps: List[Union[TestStepSpec, Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Create a new test case from a list of steps.

    Builds the nested `attributes.test_step` structure and calls the TaskTracker
    create API. Steps can be TestStepSpec instances or dicts with
    step_description, step_data, step_result.
    """
    payload = deepcopy(test_case_base)
    attributes = payload.setdefault("attributes", {})
    attributes["test_step"] = build_test_steps(steps)
    return create_test_case(suit=suit, test_case_json=payload)


def build_patch_steps(steps: List[Union[TestStepSpec, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Build the TaskTracker update patch `attributes.test_step.testStepList` from step specs.

    Update API expects each step to have stepDescription/stepData/stepResult with
    formattedText (ProseMirror JSON string) and plainText. Accepts TestStepSpec or dicts.
    """
    result: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps, start=1):
        if isinstance(step, dict):
            spec = TestStepSpec(
                step_description=step.get("step_description", ""),
                step_data=step.get("step_data", ""),
                step_result=step.get("step_result", ""),
            )
        else:
            spec = step
        fmt_desc = build_formatted_text(spec.step_description)
        fmt_data = build_formatted_text(spec.step_data or "")
        fmt_result = build_formatted_text(spec.step_result)
        result.append(
            {
                "code": str(uuid4()),
                "stepDescription": {
                    "formattedText": fmt_desc,
                    "plainText": spec.step_description.strip(),
                },
                "stepData": {
                    "formattedText": fmt_data,
                    "plainText": (spec.step_data or "").strip(),
                },
                "stepResult": {
                    "formattedText": fmt_result,
                    "plainText": spec.step_result.strip(),
                },
                "callToTestId": None,
                "stepNumber": idx,
                "stepType": "step_by_step",
                "files": None,
                "deleted": False,
                "stepFiles": [],
            }
        )
    return result


def update_test_case_from_steps(
    code: str,
    steps: List[Union[TestStepSpec, Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Update an existing test case's steps by code.

    Builds the patch body in the shape expected by the TaskTracker update API
    (attributes.test_step.testStepList) and calls update_test_case.
    """
    patch = {
        "attributes": {
            "test_step": {
                "testStepList": build_patch_steps(steps),
            }
        }
    }
    return update_test_case(code=code, patch_json=patch)
