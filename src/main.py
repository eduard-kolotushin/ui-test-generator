from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from typing import Any, Dict

from dotenv import load_dotenv
from langgraph.types import Command

from src.agent.graph import build_agent, run_once, run_until_done
from src.config import get_runs_dir
from src.run_artifacts import (
    create_run_dir,
    extract_created_tests_from_result,
    extract_plan_from_result,
    write_created_tests,
    write_failure_reason,
    write_plan,
)

logging.basicConfig(level=logging.INFO)


def _message_content(msg: Any) -> Any:
    """Extract content from a message (dict or LangChain message object)."""
    if isinstance(msg, dict):
        return msg.get("content")
    return getattr(msg, "content", None)


def _serializable_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert LangGraph result to JSON-serializable dict (messages as role/content)."""
    out: Dict[str, Any] = {}
    for key, value in result.items():
        if key == "messages" and isinstance(value, list):
            out[key] = [
                {"type": type(m).__name__, "content": _message_content(m)}
                for m in value
            ]
        elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
            out[key] = value
        else:
            out[key] = str(value)
    return out


def _pretty_print_result(result: Dict[str, Any]) -> None:
    """
    Best-effort pretty-printer for the deep agent's output.

    Deep Agents returns a LangGraph-style state; we print the final message
    content if we can find it, otherwise we dump a JSON-serializable view.
    """
    messages = result.get("messages")
    if isinstance(messages, list) and messages:
        last = messages[-1]
        content = _message_content(last)
        if content:
            print(content)
            return

    # Fallback: dump a serializable view of the state
    print(json.dumps(_serializable_result(result), ensure_ascii=False, indent=2))


def _build_user_message_from_task_code(task_code: str) -> str:
    """Fetch unit by code and build user message from summary and description."""
    from src.tasktracker.tools import get_test_case

    unit = get_test_case(task_code)
    summary = unit.get("summary") or ""
    description = unit.get("description") or unit.get("descriptionPlain") or ""
    parts = [f"Task {task_code}:", summary]
    if description:
        parts.append(str(description))
    return "\n\n".join(p for p in parts if p).strip()


def _single_run_main(args: argparse.Namespace) -> int:
    """Run single-run mode: resolve input, run agent with auto-approve, write artifacts."""
    import os

    load_dotenv()

    if not args.task_code and not args.prompt:
        print("Error: provide --task-code and/or --prompt.", file=sys.stderr)
        return 1

    dry_run = getattr(args, "dry_run", False)
    if dry_run:
        os.environ["TASKTRACKER_DRY_RUN"] = "true"
        print("Dry run: no test cases or folders will be created in TaskTracker; artifacts will be written.", file=sys.stderr)

    output_dir = args.output_dir or get_runs_dir()
    run_id = args.run_id or str(uuid.uuid4())
    run_dir = create_run_dir(output_dir, run_id)

    failed = False
    failure_parts = []
    result = {}

    try:
        # Resolve user message (--task-code fetches real task from TaskTracker even in dry-run)
        if args.task_code and args.prompt:
            task_msg = _build_user_message_from_task_code(args.task_code)
            user_message = f"{task_msg}\n\nAdditional requirement: {args.prompt}"
        elif args.task_code:
            user_message = _build_user_message_from_task_code(args.task_code)
        else:
            user_message = args.prompt

        agent = build_agent()
        payload = {
            "messages": [
                {"role": "user", "content": user_message},
            ]
        }
        config = {"configurable": {"thread_id": run_id}}
        result = run_until_done(agent, payload, config, auto_approve=True)
    except Exception as e:
        failed = True
        failure_parts.append(f"Exception: {e}")
        import traceback
        failure_parts.append(traceback.format_exc())

    # Write plan and created_tests in all cases
    plan_content = extract_plan_from_result(result)
    if plan_content:
        write_plan(run_dir, plan_content)
    elif failed:
        write_plan(run_dir, "Run failed. See failure_reason.txt.")

    created_tests = extract_created_tests_from_result(result)
    write_created_tests(run_dir, created_tests)

    if failed:
        failure_content = "\n\n".join(failure_parts)
        last_plan = extract_plan_from_result(result)
        if last_plan:
            failure_content += "\n\nLast agent message:\n" + last_plan
        write_failure_reason(run_dir, failure_content)
        print(f"Single run failed. Artifacts in {run_dir}", file=sys.stderr)
        return 1

    # Optional: treat as failed if agent reported failure in message (heuristic)
    if plan_content and (
        "could not" in plan_content.lower()
        or "failed" in plan_content.lower()
        or "cannot" in plan_content.lower()
    ):
        write_failure_reason(run_dir, plan_content)
        failed = True

    if dry_run:
        print(f"Dry run {run_id} finished. Artifacts in {run_dir}")
    else:
        print(f"Run {run_id} finished. Artifacts in {run_dir}")
    return 0 if not failed else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Deep Agents-based UI test generator for TaskTracker. "
            "Provide a natural language instruction and the agent will "
            "use TaskTracker tools to generate or update test cases."
        )
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="One-shot instruction for the agent "
        '(e.g. "Generate tests in folder X based on folder Y").',
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in a simple REPL loop instead of one-shot mode (chat with history).",
    )
    parser.add_argument(
        "--thread-id",
        help=(
            "Optional thread id for chat history. "
            "If omitted in interactive mode, a random id is generated."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    single_run_parser = subparsers.add_parser(
        "single-run",
        help="Non-interactive run: task code or prompt in, artifacts (plan, created tests, failure reason) out.",
    )
    single_run_parser.add_argument(
        "--task-code",
        metavar="CODE",
        help="Task/unit code to fetch (e.g. PVM-123); content used as requirement.",
    )
    single_run_parser.add_argument(
        "--prompt",
        help="Raw requirement text (or additional requirement when used with --task-code).",
    )
    single_run_parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Output directory for run artifacts (default: env UI_TEST_RUNS_DIR or {get_runs_dir()!r}).",
    )
    single_run_parser.add_argument(
        "--run-id",
        default=None,
        help="Explicit run id (default: UUID).",
    )
    single_run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not create or update anything in TaskTracker (read-only + fake create/update). --task-code still fetches the real task. Artifacts are written.",
    )

    args = parser.parse_args()

    if args.command == "single-run":
        exit_code = _single_run_main(args)
        sys.exit(exit_code)

    # Load environment variables from a local `.env` file if present,
    # so config helpers can pick them up via os.getenv.
    load_dotenv()

    agent = build_agent()

    if args.interactive:
        thread_id = args.thread_id or str(uuid.uuid4())
        print(f"Starting interactive UI Test Generator. Thread id: {thread_id}")
        print("Starting interactive UI Test Generator. Type Ctrl+C to exit.")
        config = {"configurable": {"thread_id": thread_id}}
        try:
            while True:
                line = input("> ").strip()
                if not line:
                    continue

                # First, invoke the agent with the user's message.
                result = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": line,
                            }
                        ]
                    },
                    config=config,
                )

                # Handle human-in-the-loop interrupts for mutating tools.
                while result.get("__interrupt__"):
                    interrupts = result["__interrupt__"][0].value
                    action_requests = interrupts["action_requests"]
                    review_configs = interrupts["review_configs"]

                    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

                    decisions = []
                    for idx, action in enumerate(action_requests, start=1):
                        review_config = config_map.get(action["name"], {})
                        allowed = review_config.get(
                            "allowed_decisions", ["approve", "edit", "reject"]
                        )
                        print(
                            f"\nPending tool call #{idx}: {action['name']}"
                            f"\n  args: {json.dumps(action['args'], ensure_ascii=False)}"
                            f"\n  allowed decisions: {allowed}\n"
                        )
                        while True:
                            choice = (
                                input(
                                    f"Decision for {action['name']} "
                                    f"({', '.join(allowed)}): "
                                )
                                .strip()
                                .lower()
                            )
                            if choice not in allowed:
                                print("Invalid choice, try again.")
                                continue

                            if choice == "edit":
                                # Let the user edit the tool arguments as JSON.
                                print(
                                    "Enter edited args as JSON. "
                                    "Press Enter to keep the original args."
                                )
                                while True:
                                    edited = input("Edited args JSON: ").strip()
                                    if not edited:
                                        edited_args = action["args"]
                                        break
                                    try:
                                        edited_args = json.loads(edited)
                                        if not isinstance(edited_args, dict):
                                            print(
                                                "Edited args must be a JSON object "
                                                "(e.g. {\"key\": \"value\"})."
                                            )
                                            continue
                                        break
                                    except json.JSONDecodeError as e:
                                        print(f"Invalid JSON: {e}. Try again.")

                                decisions.append(
                                    {
                                        "type": "edit",
                                        "edited_action": {
                                            "name": action["name"],
                                            "args": edited_args,
                                        },
                                    }
                                )
                            else:
                                decisions.append({"type": choice})
                            break

                    # Resume execution with the collected decisions.
                    result = agent.invoke(
                        Command(resume={"decisions": decisions}),
                        config=config,
                    )

                _pretty_print_result(result)
        except KeyboardInterrupt:
            print("\nExiting.")
    else:
        if not args.prompt:
            parser.error("You must provide PROMPT or use --interactive.")
        # One-shot mode: you can optionally pass a thread id to reuse history
        result = run_once(agent, args.prompt, thread_id=args.thread_id)
        _pretty_print_result(result)


if __name__ == "__main__":
    main()

