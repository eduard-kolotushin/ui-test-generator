#!/usr/bin/env python3
"""Seed the TaskTracker stub with sample folders and realistic Grafana datasource test cases.

Run with: uv run python stub_servers/tasktracker/seed_sample_data.py
Stub server must be running: uv run uvicorn stub_servers.tasktracker.app:app --port 8000
"""
from __future__ import annotations

import os
import sys

import httpx

BASE_URL = os.getenv("TASKTRACKER_STUB_URL", "http://localhost:8000")

FOLDERS = [
    {"name": "postgres datasource", "parent_id": None},
    {"name": "prometheus datasource", "parent_id": None},
    {"name": "abyss datasource", "parent_id": None},
]

TEST_CASES = [
    # --- postgres datasource ---
    {
        "folder": "postgres datasource",
        "name": "Datasource connection and Save & Test",
        "description": "Verify Postgres datasource connects and health check passes in Configuration.",
        "steps": [
            "Navigate to Configuration → Data sources",
            "Click Add data source and select PostgreSQL",
            "Fill host, database, user, and SSL mode",
            "Click Save & Test",
            "Verify green banner 'Database Connection OK'",
        ],
    },
    {
        "folder": "postgres datasource",
        "name": "Explore SQL query returns table",
        "description": "Run a simple SQL query in Explore and confirm table result appears.",
        "steps": [
            "Open Explore from sidebar or dashboard panel",
            "Select PostgreSQL datasource",
            "Enter query: SELECT 1 AS value",
            "Click Run query",
            "Verify Table view shows one row with column 'value'",
        ],
    },
    {
        "folder": "postgres datasource",
        "name": "Table panel with SQL and time column",
        "description": "Add a table panel using Postgres query and optional time column for dashboard time range.",
        "steps": [
            "Create or edit a dashboard",
            "Add visualization → Table",
            "Set datasource to PostgreSQL",
            "Enter query with time column e.g. SELECT time, metric FROM series WHERE $__timeFilter(time)",
            "Apply and set dashboard time range",
            "Verify table renders with correct columns and rows",
        ],
    },
    {
        "folder": "postgres datasource",
        "name": "Time series panel from Postgres query",
        "description": "Build a time series graph from a Postgres query with time and value columns.",
        "steps": [
            "Add panel and choose Time series visualization",
            "Select PostgreSQL datasource",
            "Write query returning time column and at least one value column",
            "Map Format as: Time series in query options",
            "Apply and verify graph renders for current time range",
        ],
    },
    {
        "folder": "postgres datasource",
        "name": "Dashboard variable from Postgres query",
        "description": "Create a dropdown variable backed by a Postgres query and use it in a panel.",
        "steps": [
            "Edit dashboard → Variables → Add variable",
            "Set type to Query, datasource to PostgreSQL",
            "Enter query e.g. SELECT DISTINCT name FROM services",
            "Save and apply variable",
            "Add panel with query that uses variable (e.g. WHERE service = '$service')",
            "Change variable value and verify panel updates",
        ],
    },
    # --- prometheus datasource ---
    {
        "folder": "prometheus datasource",
        "name": "Prometheus datasource connection",
        "description": "Verify Prometheus URL and connection in Configuration.",
        "steps": [
            "Go to Configuration → Data sources",
            "Add data source → Prometheus",
            "Set URL (e.g. http://prometheus:9090) and access mode",
            "Click Save & Test",
            "Verify 'Data source is working'",
        ],
    },
    {
        "folder": "prometheus datasource",
        "name": "Explore PromQL and switch instant/range",
        "description": "Run PromQL in Explore and toggle between instant and range query.",
        "steps": [
            "Open Explore and select Prometheus",
            "Enter query e.g. up",
            "Click Run query, verify time series or table result",
            "Switch query type to Instant and run again",
            "Verify result matches instant query semantics",
        ],
    },
    {
        "folder": "prometheus datasource",
        "name": "Time series panel with legend and time range",
        "description": "Add a Prometheus-backed graph and check legend and time range behavior.",
        "steps": [
            "Add panel → Time series, datasource Prometheus",
            "Add query e.g. rate(http_requests_total[5m])",
            "Apply and verify graph renders",
            "Check legend shows series names and values",
            "Change dashboard time range and verify graph updates",
        ],
    },
    {
        "folder": "prometheus datasource",
        "name": "Multiple queries and legend format",
        "description": "Panel with several PromQL queries and custom legend format.",
        "steps": [
            "Add Time series panel with Prometheus",
            "Add two queries e.g. rate(a_total[5m]), rate(b_total[5m])",
            "Set Legend mode and format e.g. {{job}} - {{instance}}",
            "Apply and verify both series appear with formatted legend",
            "Toggle legend values (e.g. Last, Mean) and verify values update",
        ],
    },
    {
        "folder": "prometheus datasource",
        "name": "Alert rule using Prometheus query",
        "description": "Create an alert that evaluates a Prometheus expression.",
        "steps": [
            "Edit dashboard and add panel with Prometheus query",
            "Open panel → Alert tab → Create alert rule",
            "Set condition (e.g. WHEN last() OF query A IS ABOVE 1)",
            "Configure contact point and save",
            "Trigger condition if possible and verify notification or state change",
        ],
    },
    # --- abyss datasource ---
    {
        "folder": "abyss datasource",
        "name": "Abyss datasource connection and health",
        "description": "Verify Abyss datasource configuration and health check.",
        "steps": [
            "Navigate to Configuration → Data sources",
            "Add or select Abyss datasource",
            "Fill required connection settings (URL, auth if any)",
            "Click Save & Test",
            "Verify success message or health indicator",
        ],
    },
    {
        "folder": "abyss datasource",
        "name": "Explore query returns data",
        "description": "Run a query in Explore and confirm result format.",
        "steps": [
            "Open Explore and select Abyss datasource",
            "Enter a valid query (e.g. default or example from docs)",
            "Click Run query",
            "Verify result appears as table or time series as expected",
        ],
    },
    {
        "folder": "abyss datasource",
        "name": "Dashboard panel using Abyss query",
        "description": "Add a panel that uses Abyss and responds to time range.",
        "steps": [
            "Create or edit dashboard, add new panel",
            "Set datasource to Abyss",
            "Configure query and visualization type",
            "Apply and set dashboard time range",
            "Verify panel renders and updates when time range changes",
        ],
    },
]


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        for f in FOLDERS:
            r = client.post("/folders", json=f)
            r.raise_for_status()
            print(f"Created folder: {r.json().get('name', f)}")

        for tc in TEST_CASES:
            r = client.post("/test-cases", json=tc)
            r.raise_for_status()
            print(f"  Created test case: {tc['name']} ({tc['folder']})")

    print(f"\nDone. {len(FOLDERS)} folders, {len(TEST_CASES)} test cases at {BASE_URL}")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError as e:
        print(f"Could not connect to {BASE_URL}. Start the stub first:\n  uv run uvicorn stub_servers.tasktracker.app:app --port 8000", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)
