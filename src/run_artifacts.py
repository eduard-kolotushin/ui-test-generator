"""
Helpers to create and write single-run artifacts: plan, created tests, failure reason.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def create_run_dir(output_dir: str | Path, run_id: str) -> Path:
    """Create output_dir/run_id and return the path."""
    path = Path(output_dir) / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_plan(run_dir: Path, content: str) -> Path:
    """Write plan content to run_dir/plan.md."""
    out = run_dir / "plan.md"
    out.write_text(content, encoding="utf-8")
    return out


def write_created_tests(run_dir: Path, created_tests: List[Dict[str, Any]]) -> Path:
    """Write list of {tool, args, result} to run_dir/created_tests.json."""
    out = run_dir / "created_tests.json"
    out.write_text(json.dumps(created_tests, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def write_failure_reason(run_dir: Path, content: str) -> Path:
    """Write failure reason to run_dir/failure_reason.txt."""
    out = run_dir / "failure_reason.txt"
    out.write_text(content, encoding="utf-8")
    return out


def _message_content(msg: Any) -> Any:
    """Extract content from a message (dict or object)."""
    if isinstance(msg, dict):
        return msg.get("content")
    return getattr(msg, "content", None)


def _message_tool_calls(msg: Any) -> List[Dict[str, Any]]:
    """Extract tool_calls from an AI message (dict or object)."""
    if isinstance(msg, dict):
        return msg.get("tool_calls") or msg.get("additional_kwargs", {}).get("tool_calls") or []
    return getattr(msg, "tool_calls", None) or []


def _message_tool_call_id(msg: Any) -> Any:
    """Extract tool_call_id from a tool message (dict or object)."""
    if isinstance(msg, dict):
        return msg.get("tool_call_id")
    return getattr(msg, "tool_call_id", None)


def _message_type(msg: Any) -> str:
    """Get message type name (AIMessage, ToolMessage, HumanMessage, etc.)."""
    if isinstance(msg, dict):
        return msg.get("type", msg.get("id", [""])[0] if isinstance(msg.get("id"), list) else "")
    return type(msg).__name__


def extract_plan_from_result(result: Dict[str, Any]) -> str:
    """
    Extract plan / reasoning from the agent result state.

    Uses the last assistant message content as the plan (full response including
    plan section and summary). If no messages, returns empty string.
    """
    messages = result.get("messages") or []
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        kind = _message_type(msg)
        if kind in ("AIMessage", "ai"):
            content = _message_content(msg)
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if isinstance(text, str) and text.strip():
                            parts.append(text)
                if parts:
                    return "\n\n".join(parts)
            break
    return ""


def extract_created_tests_from_result(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract create_test_case and update_test_case tool calls and their results
    from the final messages in the agent state.

    Returns a list of {"tool": "create_test_case"|"update_test_case", "args": {...}, "result": ...}.
    result is the raw tool response (string or parsed dict if JSON).
    """
    messages = result.get("messages") or []
    # Build map: tool_call_id -> result content (from ToolMessage)
    tool_results: Dict[str, Any] = {}
    for msg in messages:
        if _message_type(msg) not in ("ToolMessage", "tool"):
            continue
        tid = _message_tool_call_id(msg)
        if tid is not None:
            content = _message_content(msg)
            if isinstance(content, str) and content.strip():
                try:
                    content = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    pass
            tool_results[tid] = content

    # Collect tool_calls from AIMessage for create_test_case / update_test_case
    created: List[Dict[str, Any]] = []
    for msg in messages:
        if _message_type(msg) not in ("AIMessage", "ai"):
            continue
        for tc in _message_tool_calls(msg):
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            if name not in ("create_test_case", "update_test_case"):
                continue
            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}) or {}
            tid = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
            result_content = tool_results.get(tid) if tid else None
            created.append({
                "tool": name,
                "args": args,
                "result": result_content,
            })
    return created
