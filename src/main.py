from __future__ import annotations

import argparse
import json
import uuid
from typing import Any, Dict

from dotenv import load_dotenv
from langgraph.types import Command

from src.agent.graph import build_agent, run_once


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
    args = parser.parse_args()

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

