from __future__ import annotations

from typing import Any, Dict, Optional, Set
import httpx

from deepagents import create_deep_agent
from langgraph.types import Command
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_gigachat import GigaChat
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import (
    create_folder_tool,
    create_test_case_tool,
    get_root_folder_units_tool,
    get_single_test_case_tool,
    get_test_cases_tool,
    update_test_case_tool,
)
from src.config import (
    get_gigachat_credentials,
    get_gigachat_verify_ssl,
    get_hub_api_key,
    get_hub_base_url,
    get_hub_verify_ssl,
    get_model_name,
    get_postgres_checkpoint_url,
    get_postgres_store_url,
)


GIGACHAT_MODELS: Set[str] = {"GigaChat-2", "GigaChat-2-Pro", "GigaChat-2-Max"}

_CHECKPOINTER_CM: Optional[Any] = None
_CHECKPOINTER: Optional[Any] = None
_STORE_CM: Optional[Any] = None
_STORE: Optional[Any] = None


def build_gigachat_model(model_name: str) -> GigaChat:
    """
    Construct a LangChain-compatible GigaChat model using env-based config.
    """
    return GigaChat(
        model=model_name,
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
    global _CHECKPOINTER_CM, _CHECKPOINTER

    dsn = get_postgres_checkpoint_url()
    if not dsn:
        return InMemorySaver()

    if _CHECKPOINTER is not None:
        return _CHECKPOINTER

    try:
        from langgraph.checkpoint.postgres import (  # type: ignore[import]
            PostgresSaver,
        )
    except ImportError:  # pragma: no cover - optional dependency
        return InMemorySaver()

    # from_conn_string returns a context manager; keep it in a module-level
    # variable so the underlying saver (and its pool) stay alive.
    _CHECKPOINTER_CM = PostgresSaver.from_conn_string(dsn)
    _CHECKPOINTER = _CHECKPOINTER_CM.__enter__()
    _CHECKPOINTER.setup()
    return _CHECKPOINTER


def build_hub_model(model_name: str) -> ChatOpenAI:
    """
    Construct a ChatOpenAI model pointed at an OpenAI-compatible HUB.

    The HUB is configured via `HUB_BASE_URL` and `HUB_API_KEY` env vars and
    can host OSS models like Qwen, Code Llama, etc.
    """
    base_url = get_hub_base_url()
    api_key = get_hub_api_key()
    verify = get_hub_verify_ssl()
    http_client = httpx.Client(verify=verify, timeout=600)
    return ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        http_client=http_client,
        timeout=600,
    )


def build_model() -> Any:
    """
    Select the LLM to use based on `LLM_MODEL`.

    If the model name is one of the GigaChat family, use GigaChat; otherwise
    treat it as a HUB model served via an OpenAI-compatible endpoint.
    """
    model_name = get_model_name()
    if model_name in GIGACHAT_MODELS:
        return build_gigachat_model(model_name)
    return build_hub_model(model_name)


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
    global _STORE_CM, _STORE

    dsn = get_postgres_store_url()
    if not dsn:
        return InMemoryStore()

    if _STORE is not None:
        return _STORE

    try:
        from langgraph.store.postgres import (  # type: ignore[import]
            PostgresStore,
        )
    except ImportError:  # pragma: no cover - optional dependency
        return InMemoryStore()

    # from_conn_string returns a context manager; keep it in a module-level
    # variable so the underlying store (and its pool) stay alive.
    _STORE_CM = PostgresStore.from_conn_string(dsn)
    _STORE = _STORE_CM.__enter__()
    _STORE.setup()
    return _STORE


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

    model = build_model()
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
        # Human-in-the-loop interrupts on mutating TaskTracker operations.
        # For these tools the agent will pause and request approval/edit/reject
        # before executing the call.
        interrupt_on={
            "create_folder": True,
            "create_test_case": True,
            "update_test_case": True,
        },
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


def run_until_done(
    agent: Any,
    payload: Dict[str, Any],
    config: Dict[str, Any],
    *,
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """
    Run the agent until no interrupt is pending.

    If `auto_approve` is True, any human-in-the-loop interrupt is resolved
    by approving all pending tool calls. Otherwise callers must handle
    `result["__interrupt__"]` themselves (e.g. interactive REPL).
    """
    result = agent.invoke(payload, config)
    while result.get("__interrupt__") and auto_approve:
        interrupts = result["__interrupt__"][0].value
        action_requests = interrupts["action_requests"]
        decisions = [{"type": "approve"} for _ in action_requests]
        result = agent.invoke(
            Command(resume={"decisions": decisions}),
            config=config,
        )
    return result

