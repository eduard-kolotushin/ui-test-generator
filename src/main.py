from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from src.agent.graph import build_agent, run_once


def _pretty_print_result(result: Dict[str, Any]) -> None:
    """
    Best-effort pretty-printer for the deep agent's output.

    Deep Agents returns a LangGraph-style state; we print the final message
    content if we can find it, otherwise we dump the whole structure as JSON.
    """
    messages = result.get("messages")
    if isinstance(messages, list) and messages:
        last = messages[-1]
        content = last.get("content") if isinstance(last, dict) else None
        if content:
            print(content)
            return

    # Fallback: print raw JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))


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
        help="Run in a simple REPL loop instead of one-shot mode.",
    )
    args = parser.parse_args()

    agent = build_agent()

    if args.interactive:
        print("Starting interactive UI Test Generator. Type Ctrl+C to exit.")
        try:
            while True:
                line = input("> ").strip()
                if not line:
                    continue
                result = run_once(agent, line)
                _pretty_print_result(result)
        except KeyboardInterrupt:
            print("\nExiting.")
    else:
        if not args.prompt:
            parser.error("You must provide PROMPT or use --interactive.")
        result = run_once(agent, args.prompt)
        _pretty_print_result(result)


if __name__ == "__main__":
    main()

