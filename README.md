## UI Test Generator – TaskTracker Deep Agent

This project is an **AI agentic application** that generates **UI test cases** for the **TaskTracker** platform (a Jira-like internal system).

The agent:

- **Reads natural language requirements** (e.g. “generate tests in folder `abyss datasource` similar to `postgres datasource`”).
- Uses **Deep Agents** (built on LangChain + LangGraph) with **GigaChat** as the LLM.
- Calls **TaskTracker APIs** (described in `api-docs.yaml`) to **list, create, update, and delete** test cases.

### Stack

- **Language**: Python (managed with `uv`).
- **Agent framework**: `deepagents`.
- **LLM**: `langchain-gigachat-lc1` (GigaChat). This project pins a **local wheel** in `wheels/` (patched for [tool schema bug #55](https://github.com/ai-forever/langchain-gigachat/issues/55)); run `uv sync` to use it.
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
  - `GIGACHAT_API_KEY` – auth token.
  - `GIGACHAT_VERIFY_SSL` – `true`/`false` (controls certificate verification).
- **TaskTracker**:
  - `TASKTRACKER_BASE_URL` – base URL of the TaskTracker API (e.g. `https://portal.works.prod.sbt/swtr`).
  - `TASKTRACKER_TOKEN` – optional bearer token if your deployment requires it.

4. **Run the agent**:

```bash
uv run python -m src.main "Generate tests in folder 'abyss datasource' based on 'postgres datasource'."
```

This will construct a Deep Agent with TaskTracker tools and print the model’s final response.

### Local testing without TaskTracker (stub)

If you don’t have access to the real TaskTracker domain:

1. **Start the in-memory stub** (in a separate terminal):

```bash
uv run python -m src.tasktracker.stub
```

The stub listens on `http://127.0.0.1:8765` and implements the same endpoints the agent uses (list test cases by folder, create, get, update).

2. **Point the app at the stub** in `.env`:

```bash
TASKTRACKER_USE_STUB=true
# TASKTRACKER_BASE_URL is optional when using stub; it defaults to http://127.0.0.1:8765
```

3. Run the agent as usual; it will talk to the local stub instead of the real API.

### Deep Agents UI (optional chat UI)

You can use [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) as a web UI on top of this agent.

1. **Start the agent server** (for example with LangGraph dev, in a separate env that supports it):

```bash
langgraph dev
```

This uses `langgraph.json` and serves the `ui-test-agent` graph locally.

2. **Clone and run Deep Agents UI**:

```bash
git clone https://github.com/langchain-ai/deep-agents-ui.git
cd deep-agents-ui
yarn install            # or: npm install / pnpm install
yarn dev                # or: npm run dev
```

The UI will start on `http://localhost:3000`. Point it at your LangGraph deployment / local dev server (Deployment URL + Assistant ID) for this project to chat with the `ui-test-agent`.

