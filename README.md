## UI Test Generator – TaskTracker Deep Agent

This project is an **AI agentic application** that generates **UI test cases** for the **TaskTracker** platform (a Jira-like internal system).

The agent:

- **Reads natural language requirements** (e.g. “generate tests in folder `abyss datasource` similar to `postgres datasource`”).
- Uses **Deep Agents** (built on LangChain + LangGraph) with **GigaChat** as the LLM.
- Calls **TaskTracker APIs** (described in `api-docs.yaml`) to **list, create, update, and delete** test cases.

### Stack

- **Language**: Python (managed with `uv`).
- **Agent framework**: `deepagents`.
- **LLM**: `langchain-gigachat` (GigaChat).
- **HTTP client**: `httpx`.

### Quick start

1. **Install uv** (if you don’t have it):

```bash
pip install uv
```

2. **Install dependencies**:

```bash
uv sync
```

3. **Set environment variables** (at minimum):

- **GigaChat**:
  - `GIGACHAT_CREDENTIALS` – auth token.
  - `GIGACHAT_VERIFY_SSL` – `true`/`false` (controls certificate verification).
- **TaskTracker**:
  - `TASKTRACKER_BASE_URL` – base URL of the TaskTracker API (e.g. `https://portal.works.prod.sbt/swtr`).
  - `TASKTRACKER_TOKEN` – optional bearer token if your deployment requires it.

4. **Run the agent**:

```bash
uv run python -m src.main "Generate tests in folder 'abyss datasource' based on 'postgres datasource'."
```

This will construct a Deep Agent with TaskTracker tools and print the model’s final response.

