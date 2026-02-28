from __future__ import annotations

from typing import Any, Dict, Optional

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_gigachat import GigaChat
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from src.agent.prompts import SYSTEM_PROMPT
from src.config import (
    get_gigachat_credentials,
    get_gigachat_verify_ssl,
    get_postgres_checkpoint_url,
    get_postgres_store_url,
)
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
        model="GigaChat-2-Max",
        credentials=get_gigachat_credentials(),
        verify_ssl_certs=get_gigachat_verify_ssl(),
        scope="GIGACHAT_API_CORP",
        timeout=(10. * 60),
    )


def build_checkpointer() -> Any:
    """
    Build a LangGraph checkpointer.

    - If `POSTGRES_CHECKPOINT_URL` is set and the Postgres saver is available,
      use it so chat history persists across restarts.
    - Otherwise fall back to an in-memory saver (good for local dev).
    """
    dsn = get_postgres_checkpoint_url()
    if dsn:
        try:
            from langgraph.checkpoint.postgres import (  # type: ignore[import]
                PostgresSaver,
            )
        except ImportError:  # pragma: no cover - optional dependency
            # Fall back to in-memory if Postgres saver is not installed.
            return InMemorySaver()

        checkpointer = PostgresSaver.from_conn_string(dsn)
        # Ensure tables exist; safe to call multiple times.
        checkpointer.setup()
        return checkpointer

    return InMemorySaver()


def build_backend() -> Any:
    """
    Build a CompositeBackend that keeps most files ephemeral in state but
    persists anything under `/memories/` into the LangGraph store.

    The store itself is configured when creating the agent (InMemoryStore by
    default; you can swap in a Postgres-backed store when needed).
    """

    def factory(runtime: Any) -> Any:
        return CompositeBackend(
            default=StateBackend(runtime),
            routes={
                "/memories/": StoreBackend(runtime),
            },
        )

    return factory


def build_store() -> Any:
    """
    Build a LangGraph Store for long-term memory.

    - If `POSTGRES_STORE_URL` is set and a Postgres store implementation is
      available, use that for `/memories/*`.
    - Otherwise fall back to an in-memory store (good for local dev).
    """
    dsn = get_postgres_store_url()
    if dsn:
        try:
            from langgraph.store.postgres import (  # type: ignore[import]
                PostgresStore,
            )
        except ImportError:  # pragma: no cover - optional dependency
            return InMemoryStore()

        store = PostgresStore.from_conn_string(dsn)
        store.setup()
        return store

    return InMemoryStore()


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
    checkpointer = build_checkpointer()
    backend = build_backend()
    store = build_store()

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        skills=["skills/tasktracker"],
        checkpointer=checkpointer,
        backend=backend,
        store=store,
    )
    return agent


def run_once(agent: Any, user_message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience helper to run the agent once on a single user instruction.

    Deep Agents expects an input mapping with a `messages` key that contains
    the conversation so far.
    """
    payload = {
        "messages": [
            {
                "role": "user",
                "content": user_message,
            }
        ]
    }
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}
        return agent.invoke(payload, config)
    return agent.invoke(payload)

