## UI Test Generator – TaskTracker Deep Agent

This project is an **AI agentic application** that generates **UI test cases** for the **TaskTracker** platform (a Jira-like internal system).

The agent:

- **Reads natural language requirements** (e.g. “generate tests in folder `abyss datasource` similar to `postgres datasource`”).
- Uses **Deep Agents** (built on LangChain + LangGraph) with **GigaChat** as the LLM.
- Talks to **TaskTracker** only via the **TaskTracker MCP server**: the same tools are exposed as an MCP server (for Cursor and other clients) and used in-process by the Deep Agent.

### Stack

- **Language**: Python (managed with `uv`).
- **Agent framework**: `deepagents`.
- **LLM**:
  - Default: `GigaChat-2` via `langchain-gigachat-lc1` (local wheel in `wheels/`, patched for [tool schema bug #55](https://github.com/ai-forever/langchain-gigachat/issues/55)).
  - Other models: any OpenAI-compatible model served from your **HUB** (Qwen, Code Llama, etc.) via `langchain-openai`.
- **HTTP client**: `httpx`.

### Quick start

1. **Install uv** (if you don’t have it):

```bash
pip install uv
export PATH="$HOME/Library/Python/3.13/bin:$PATH"
```

2. **Install dependencies**:

```bash
uv sync
```

3. **Set environment variables** (at minimum):

- **Model selection**:
  - `LLM_MODEL` – name of the model to use. Defaults to `GigaChat-2`. If the value is one of `["GigaChat-2", "GigaChat-2-Pro", "GigaChat-2-Max"]`, the agent uses GigaChat; otherwise it uses your HUB (see below).
- **GigaChat** (used when `LLM_MODEL` is a GigaChat model):
  - `GIGACHAT_API_KEY` – auth token.
  - `GIGACHAT_VERIFY_SSL` – `true`/`false` (controls certificate verification).
- **HUB (OpenAI-compatible OSS models)** – used when `LLM_MODEL` is *not* a GigaChat model:
  - `HUB_BASE_URL` – base URL of your HUB, e.g. `http://localhost:12434/v1`.
  - `HUB_API_KEY` – API key for the HUB (dummy value is fine if your HUB doesn’t enforce auth).
- **TaskTracker**:
  - `TASKTRACKER_BASE_URL` – base URL of the TaskTracker API (e.g. `https://portal.works.prod.sbt/swtr`).
  - `TASKTRACKER_TOKEN` – optional bearer token if your deployment requires it.
  - `TASKTRACKER_BASIC_AUTH` – optional `user:password` for HTTP Basic auth (overrides token when set).
  - `TASKTRACKER_DRY_RUN` – set to `true` to stub mutating calls (create/update) while reads go to the real API.
- **Single-run mode** (optional):
  - `UI_TEST_RUNS_DIR` – directory for run artifacts (default: `runs`). See [Single-run mode](#single-run-mode-non-interactive).

4. **Run the agent**:

```bash
uv run python -m src.main single-run --prompt "Generate tests in folder 'abyss datasource' based on 'postgres datasource'."
```

This will construct a Deep Agent with TaskTracker tools and print the model’s final response.

### Single-run mode (non-interactive)

You can run the agent in a **single run** without any user interaction: it takes a task code or raw requirement, runs until done (auto-approving tool calls), and writes artifacts to the filesystem.

**Options:**

- **By task code** – the agent gets the task/unit content from TaskTracker and designs tests from it:

```bash
uv run python -m src.main single-run --task-code PVM-123
```

- **By raw prompt** – you pass the requirement text directly (e.g. paste from a wiki):

```bash
uv run python -m src.main single-run --prompt "Add smoke tests for the new login flow."
```

- **Both** – task code for context plus an extra requirement:

```bash
uv run python -m src.main single-run --task-code PVM-123 --prompt "Focus on negative cases."
```

**Artifacts** are written under an output directory (default: `runs`, or `UI_TEST_RUNS_DIR` in `.env`). Each run gets a subfolder (by default a UUID) with:

- `plan.md` – agent's plan and reasoning
- `created_tests.json` – list of created/updated test cases (tool name, args, result)
- `failure_reason.txt` – only if the run failed (exception or agent-reported failure)

**CLI flags:**

- `--output-dir DIR` – override the output directory (default: env `UI_TEST_RUNS_DIR` or `runs`)
- `--run-id ID` – use a fixed run id instead of a generated UUID
- `--dry-run` – do not create or update anything in TaskTracker (read-only; `--task-code` still fetches the real task). Use to get plan and created_tests.json without writing to TaskTracker.

Example with custom output dir and run id:

```bash
uv run python -m src.main single-run --prompt "List root folders" --output-dir ./my-runs --run-id my-run-1
```

Dry run (fetch real task, plan and artifacts only; no test cases created in TaskTracker):

```bash
uv run python -m src.main single-run --task-code PVM-123 --dry-run
```

### TaskTracker MCP server

TaskTracker operations (folders, test cases, create/update) are implemented as an **MCP server** so Cursor and other MCP hosts can use them directly. The Deep Agent uses the same tool implementations in-process (no separate MCP process when running the CLI).

**Run the MCP server** (e.g. for Cursor):

```bash
uv run python -m src.mcp.tasktracker_server
```

The server uses **stdio** by default. Configure the same environment variables as for the agent (`TASKTRACKER_BASE_URL`, `TASKTRACKER_TOKEN` or `TASKTRACKER_BASIC_AUTH`, and optionally `TASKTRACKER_USE_STUB=true` or `TASKTRACKER_DRY_RUN=true`).

**Add to Cursor’s MCP settings** (e.g. in `.cursor/mcp.json` or Cursor Settings → MCP):

```json
{
  "mcpServers": {
    "tasktracker-ui-tests": {
      "command": "uv",
      "args": ["--directory", "C:/path/to/ui-test-generator", "run", "python", "-m", "src.mcp.tasktracker_server"]
    }
  }
}
```

Use the project root as `--directory` so `uv run` resolves the app and env.

**Tools exposed:** `get_root_folder_units`, `create_folder`, `get_test_cases`, `get_test_case`, `create_test_case`, `update_test_case_from_steps`.

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

4. **Call the stub from Cursor:** Open **`api/tasktracker-stub.http`**, install the **REST Client** extension (Huachao Mao) if needed, then click **Send Request** above any request. (Thunder Client free version does not support Cursor.)

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

