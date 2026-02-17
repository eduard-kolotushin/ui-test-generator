# Stub servers for external services

REST API stubs for development and testing without real backends.

## TaskTracker

Stub for the TaskTracker API: folders (nested) and test cases.

**Run (from project root):**

```bash
uv run uvicorn stub_servers.tasktracker.app:app --reload --port 8000
```

- **Folders:** `GET/POST /folders`, `GET/PUT/DELETE /folders/{id}`. Nested via `parent_id`.
- **Test cases:** `GET/POST /test-cases`, `GET/PUT/DELETE /test-cases/{id}`. Schema: `folder`, `name`, `description`, `steps` (list of strings).

Base URL: `http://localhost:8000`. OpenAPI: `http://localhost:8000/docs`.

### Sample data

- **Seed script:** `uv run python stub_servers/tasktracker/seed_sample_data.py` (stub must be running). Creates 3 folders and 13 realistic Grafana datasource test cases (Postgres, Prometheus, Abyss).
- **Request files:** `stub_servers/tasktracker/sample_requests/*.http` – same requests for REST Client or manual use. See `sample_requests/README.md`.
