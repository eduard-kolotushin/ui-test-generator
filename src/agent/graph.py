from __future__ import annotations

from typing import Any, Dict

from deepagents import create_deep_agent
from langchain_gigachat import GigaChat

from src.agent.prompts import SYSTEM_PROMPT
from src.config import get_gigachat_credentials, get_gigachat_verify_ssl
from src.tasktracker.tools import (
    create_folder_tool,
    create_test_case_tool,
    get_root_folder_units_tool,
    get_single_test_case_tool,
    get_test_cases_tool,
    update_test_case_tool,
)


def build_gigachat_model() -> GigaChat:
    """
    Construct a LangChain-compatible GigaChat model using env-based config.
    """
    return GigaChat(
        credentials=get_gigachat_credentials(),
        verify_ssl_certs=get_gigachat_verify_ssl(),
        scope="GIGACHAT_API_CORP",
    )


def build_agent() -> Any:
    """
    Create the deep agent graph wired with TaskTracker tools and GigaChat.

    Returns a LangGraph runnable that you can `.invoke` or `.stream`.
    """
    tools = [
        get_root_folder_units_tool(),
        create_folder_tool(),
        get_test_cases_tool(),
        get_single_test_case_tool(),
        create_test_case_tool(),
        update_test_case_tool(),
    ]

    model = build_gigachat_model()

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        # Attach the TaskTracker skill so the agent can load
        # more detailed, task-specific instructions on demand.
        skills=["skills/tasktracker"],
    )
    return agent


def run_once(agent: Any, user_message: str) -> Dict[str, Any]:
    """
    Convenience helper to run the agent once on a single user instruction.

    Deep Agents expects an input mapping with a `messages` key that contains
    the conversation so far.
    """
    return agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ]
        }
    )

