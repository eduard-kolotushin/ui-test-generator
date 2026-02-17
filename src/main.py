"""CLI entrypoint: run the UI test generation agent with a user message."""
from typing import Any


import argparse
import json
import sys

from src.agent import create_agent, run_agent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UI Test Generator: AI agent that generates Grafana UI test cases via TaskTracker."
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="User request, e.g.: Generate tests in folder 'abyss datasource' similar to 'postgres datasource'",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=None,
        help="Model id, e.g. openai:gpt-4o-mini or anthropic:claude-3-5-sonnet-20241022",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive mode: prompt for message if not provided",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output final state as JSON (for debugging)",
    )
    args = parser.parse_args()

    message = args.message
    if not message and args.interactive:
        message = input("Your request: ").strip()
    if not message:
        parser.error("Provide a message as argument or use -i for interactive mode.")

    try:
        result = run_agent(user_message=message, model_id=args.model)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # Serialize state for debugging (messages are not always JSON-serializable)
        out = {"messages": []}
        for m in result.get("messages", []):
            try:
                out["messages"].append(
                    {"type": type(m).__name__, "content": getattr(m, "content", str(m))}
                )
            except Exception:
                out["messages"].append({"type": type(m).__name__, "content": str(m)})
        print(json.dumps(out, indent=2, default=str))
        return

    # Print last assistant message with content
    messages = result.get("messages", [])
    for m in reversed(messages):
        if hasattr(m, "content") and m.content and not getattr(m, "tool_calls", None):
            print(m.content)
            return
    print("(No text response in messages.)")


if __name__ == "__main__":
    main()
