# AGENTS.md – UI Test Generator – Project intentions

This file records the **intentions and design** of the UI Test Generator project so that both humans and AI agents can align on goals and behavior.

---

## Purpose

- **Goal**: Generate **UI test cases** for our **Grafana-based monitoring platform** in a structured, repeatable way.
- **How**: An **AI agent** that uses **TaskTracker’s API** to manage test cases. The agent interprets **natural language requirements** and performs the right sequence of API calls (get → reason → create/update/delete).

---

## Core workflow (by example)

**User says:**  
*"You need to generate tests in folder 'abyss datasource' that are similar to tests that exist in folder 'postgres datasource'."*

**Intended agent behavior:**

1. **Parse** the request → source folder = `postgres datasource`, target folder = `abyss datasource`.
2. **Get** all test cases from the source folder via TaskTracker API (tool: `get_test_cases('postgres datasource')`).
3. **Reason** over each (or a subset of) test case(s) and produce **new test case JSON** that:
   - Keeps the same structure and intent (steps, assertions, metadata),
   - Adapts to the target context (e.g. datasource name, query text, labels) so they are valid for “abyss datasource”.
4. **Create** each new test case in the target folder via TaskTracker API (tool: `create_test_case('abyss datasource', test_case_json)`).

So: **source folder = template; target folder = where the generated tests live.** The agent must use **only the provided tools** to read and write test cases (no out-of-band edits).

---

## Tech stack (fixed for this project)

- **Language**: Python (managed with **uv**).
- **Orchestration**: **Deep Agents** (built on LangChain + LangGraph).
- **LLM**: **GigaChat** via `langchain-gigachat`.
- **Tools / skills**: Deep Agents skills that wrap:
  - the **TaskTracker API** defined in `api-docs.yaml` (for folders, test cases, updates, deletes),
  - any supporting utilities needed for reasoning over JSON test case structures.
- **External system**: **TaskTracker** – our platform for managing tasks and test runs; it exposes an API to manage test cases.
- **MCP server**: FastMCP-based TaskTracker MCP server in `src/mcp/tasktracker_server.py` that exposes folder and test case operations as MCP tools for Cursor and other MCP hosts.
- **LangChain MCP tools**: `src/mcp/tasktracker_client_tools.py` defines LangChain `StructuredTool`s that call the MCP server in-process so the Deep Agent and MCP clients share a single authoritative TaskTracker integration path.
- **Shared step helpers**: `src/tasktracker/steps.py` centralizes building and updating TaskTracker test steps (including ProseMirror formatted text) so both the MCP server and Deep Agent use the same logic.

---

## TaskTracker API (assumed capabilities)

For the agent, TaskTracker is the **single source of truth** for test cases. We assume it supports at least:

- **Get test cases** (e.g. by folder) → returns a list of test case JSON objects.
- **Create test case** (folder + test case JSON) → returns the created test case.
- **Update test case** (id + test case JSON) → returns the updated test case.
- **Delete test case** (id) → removes the test case.

In the API, a **test case** is represented as a **JSON object** (structure defined by TaskTracker; the agent should preserve/adapt that structure when generating new tests).

The actual HTTP endpoints and payload shapes are implemented in `src/tasktracker/client.py` and can be adjusted when the real API spec is known.

---

## Agent design

- **Type**: Single deep agent created via `deepagents.create_deep_agent` that runs in a **loop** (reason → optional tool calls → reason again) until it can answer or finish the task.
- **LLM skill**: A Deep Agents-compatible chat model built on `GigaChat` (`langchain-gigachat`), configured via environment variables and `src/config.py`.
- **TaskTracker skills / tools**:
  - **Low-level HTTP client** in `src/tasktracker/client.py` (with dry-run wrapper in `src/tasktracker/dry_run_client.py`) wraps the TaskTracker REST API.
  - **MCP server** in `src/mcp/tasktracker_server.py` exposes folder and test case operations as MCP tools (e.g. `get_root_folder_units`, `create_folder`, `get_test_cases`, `get_test_case`, `create_test_case`, `update_test_case_from_steps`).
  - **LangChain MCP tools** in `src/mcp/tasktracker_client_tools.py` provide `StructuredTool`s that call the MCP server in-process; `src/agent/tools.py` now re-exports these and is marked deprecated for new code.
  - **Shared helpers** in `src/tasktracker/steps.py` and `src/tasktracker/tools.py` centralize step JSON construction and low-level API calls so both the MCP server and Deep Agent stay in sync.
  - Typical operations from the agent’s point of view:
    - `get_root_folder_units` – discover folder hierarchy and root-level units.
    - `get_test_cases` / `get_test_case` – read existing tests to use as templates.
    - `create_test_case` – create an empty test case (summary, suit, space, folder_code); then use `update_test_case_from_steps` to add steps (TaskTracker does not accept new step codes on create).
    - `update_test_case_from_steps` – add or replace steps on an existing test case by code.
- **System prompt** (see `src/agent/prompts.py`): Instructs the agent to (1) identify source and target folders, (2) fetch source tests, (3) generate adapted test case JSON, (4) create them in the target folder. It should keep JSON structure consistent with the source unless the user asks otherwise.
- **Entrypoint**: CLI in `src/main.py`; one-shot or interactive; the CLI sends user instructions to the deep agent and prints the agent’s final answer (and, optionally, debug JSON).

---

## Out of scope (for now)

- **Grafana UI automation itself** (e.g. Playwright/Selenium) – this project only **generates and manages test case definitions** via TaskTracker; execution is assumed to be elsewhere.
- **Authentication to Grafana** – not part of this agent; only TaskTracker API credentials are needed here.
- **Custom test case schema** – the agent works with “JSON representation” of a test case; the exact schema is whatever TaskTracker uses and is reflected in the client/tools.

---

## How to use this file

- **Humans**: Read this to understand why the project exists, how the agent is supposed to behave, and what is in/out of scope.
- **AI agents (e.g. in Cursor)**: Use this as **persistent context** when editing or extending the codebase – e.g. when adding tools, changing the prompt, or adapting the TaskTracker client – so that changes stay aligned with “generate UI tests for Grafana via TaskTracker from natural language requirements.”
