# Sample API requests for TaskTracker stub

Realistic Grafana datasource UI test cases. Use to populate the stub or as reference.

## Option 1: Seed script (recommended)

With the stub server running on port 8000:

```bash
uv run python stub_servers/tasktracker/seed_sample_data.py
```

Uses `TASKTRACKER_STUB_URL` (default `http://localhost:8000`). Creates 3 folders and 13 test cases (Postgres, Prometheus, Abyss).

## Option 2: .http files (REST Client)

In VS Code / Cursor, install “REST Client” and run requests from:

- **01_create_folders.http** – create folders: postgres, prometheus, abyss datasource
- **02_test_cases_postgres.http** – 5 Postgres UI tests (connection, Explore, table panel, time series, variables)
- **03_test_cases_prometheus.http** – 5 Prometheus UI tests (connection, Explore PromQL, graph/legend, multi-query, alert)
- **04_test_cases_abyss.http** – 3 Abyss (custom) datasource tests

Run in order so folders exist if your stub expects them. Test cases use **folder name** (e.g. `"postgres datasource"`) so `GET /test-cases?folder=postgres%20datasource` returns them.

## Test case shape

Each test case is a JSON object:

- **folder** (str) – folder name
- **name** (str)
- **description** (str)
- **steps** (list[str]) – UI steps as you would run them in Grafana (datasource config, Explore, panels, variables, alerts).
