"""LangGraph ReAct agent for UI test generation using TaskTracker tools."""
from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.agent.prompts import SYSTEM_PROMPT
from src.config import get_gigachat_credentials, get_gigachat_verify_ssl
from src.tasktracker.tools import get_all_tools


def _get_model(model_id: str | None = None, **kwargs: Any) -> Any:
    """Resolve chat model from model_id or env. Supports gigachat, openai, anthropic."""
    if model_id:
        if model_id.startswith("gigachat"):
            from langchain_gigachat.chat_models import GigaChat

            credentials = get_gigachat_credentials()
            if not credentials:
                raise ValueError("GIGACHAT_API_KEY or GIGACHAT_CREDENTIALS must be set in .env for GigaChat")
            return GigaChat(
                credentials=credentials,
                verify_ssl_certs=get_gigachat_verify_ssl(),
                model=model_id.split(":", 1)[-1] if ":" in model_id else "GigaChat",
                **kwargs,
            )
        if model_id.startswith("anthropic:"):
            return ChatAnthropic(model=model_id.replace("anthropic:", ""), **kwargs)
        if model_id.startswith("openai:"):
            return ChatOpenAI(model=model_id.replace("openai:", ""), **kwargs)

    # Default: GigaChat if credentials set, else OpenAI
    if get_gigachat_credentials():
        from langchain_gigachat.chat_models import GigaChat

        print(get_gigachat_credentials(), get_gigachat_verify_ssl())
        return GigaChat(
            credentials=get_gigachat_credentials(),
            verify_ssl_certs=get_gigachat_verify_ssl(),
            scope="GIGACHAT_API_CORP",
        )
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.1, **kwargs)


def create_agent(
    model_id: str | None = None,
    system_prompt: str | None = None,
    **model_kwargs: Any,
) -> Any:
    """Build a LangGraph ReAct agent with TaskTracker tools.
    model_id: e.g. 'gigachat', 'gigachat:GigaChat', 'openai:gpt-4o-mini', 'anthropic:claude-3-5-sonnet-20241022'
    """
    model = _get_model(model_id, **model_kwargs)
    tools = get_all_tools()
    prompt = system_prompt or SYSTEM_PROMPT
    return create_react_agent(model, tools=tools, prompt=prompt)


def run_agent(
    user_message: str,
    model_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the agent with one user message and return the final state."""
    agent = create_agent(model_id=model_id, **kwargs)
    result = agent.invoke({"messages": [("user", user_message)]})
    return result
