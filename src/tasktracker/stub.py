"""
In-memory TaskTracker API stub for local testing without access to the real API.

Run with:
    uv run python -m src.tasktracker.stub

Then set in .env:
    TASKTRACKER_USE_STUB=true
    TASKTRACKER_BASE_URL=http://127.0.0.1:8765
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from uvicorn import run

# In-memory store: code -> unit (full dict as returned by GET /unit/v2/{code})
_units: Dict[str, Dict[str, Any]] = {}
_next_id = 1

# Folders: code -> FolderDto (id, key, title, children). Root is TMS_test_case.
_root_code = "TMS_test_case"
_folders: Dict[str, Dict[str, Any]] = {
    _root_code: {
        "id": {"code": _root_code},
        "key": _root_code,
        "title": "Все тест-кейсы",
        "children": [],
    }
}

app = FastAPI(
    title="TaskTracker Stub",
    description="Local stub for TaskTracker TMS/unit API for testing the UI test generator.",
)


def _make_unit(code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a minimal unit dict from create payload + assigned code."""
    return {
        "code": code,
        "summary": payload.get("summary", "Stub test case"),
        "description": payload.get("description", ""),
        "suit": payload.get("suit", {"code": "test_case", "name": "Тест-кейс", "icon": "memo_pencil"}),
        "space": payload.get("space", {"code": "TMS", "name": "Простраство TMS"}),
        "attributes": payload.get("attributes", []),
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z",
        "isFavorite": False,
        **{k: v for k, v in payload.items() if k not in ("summary", "description", "suit", "space", "attributes")},
    }


def _folder_tree(code: str) -> Dict[str, Any]:
    """Build a copy of folder node and its children for API response."""
    f = _folders.get(code)
    if not f:
        return {"id": {"code": code}, "key": code, "title": code, "children": []}
    return {
        "id": dict(f["id"]),
        "key": f["key"],
        "title": f["title"],
        "children": [_folder_tree(c["code"]) for c in f["children"]],
    }


@app.post("/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/root/units")
def post_folder_root_units(body: Dict[str, Any]) -> Dict[str, Any]:
    """Return root folder hierarchy and paginated units (FolderUnitsDto)."""
    page = (body.get("unitFilters") or {}).get("page") or {}
    page_num = page.get("page", 0)
    size = page.get("size", 50)
    all_units = list(_units.values())
    start = page_num * size
    chunk = all_units[start : start + size]
    content = [{"unit": u, "attributes": [], "calculatedAttributes": []} for u in chunk]
    return {
        "folderHierarchy": _folder_tree(_root_code),
        "units": {
            "content": content,
            "pageSize": size,
            "pageNumber": page_num,
            "hasNext": start + len(chunk) < len(all_units),
            "totalElements": len(all_units),
        },
    }


@app.post("/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/create")
def post_folder_create(body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a folder under parentId; return FolderDto."""
    name = body.get("name", "New folder")
    parent_id = body.get("parentId") or {}
    parent_code = parent_id.get("code", _root_code)
    if parent_code not in _folders:
        raise HTTPException(status_code=404, detail=f"Parent folder '{parent_code}' not found")
    code = str(uuid.uuid4()).replace("-", "")[:12]
    folder_dto = {
        "id": {"code": code},
        "key": code,
        "title": name,
        "children": [],
    }
    _folders[code] = folder_dto
    _folders[parent_code]["children"].append({"code": code})
    return folder_dto


@app.post(
    "/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/hierarchy/{folder_code}/units/filtered"
)
def post_folder_units_filtered(folder_code: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Return folder hierarchy and paginated units for the given folder."""
    page = (body.get("unitFilters") or {}).get("page") or {}
    page_num = page.get("page", 0)
    size = page.get("size", 50)
    all_units = list(_units.values())
    start = page_num * size
    chunk = all_units[start : start + size]
    content = [{"unit": u, "attributes": [], "calculatedAttributes": []} for u in chunk]
    return {
        "folderHierarchy": {
            "id": {"code": folder_code},
            "key": folder_code,
            "title": folder_code,
            "children": [],
        },
        "units": {
            "content": content,
            "pageSize": size,
            "pageNumber": page_num,
            "hasNext": start + len(chunk) < len(all_units),
            "totalElements": len(all_units),
        },
    }


@app.post("/rest/api/unit/v2/{suit}/create")
def post_unit_create(suit: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a unit (test case) and assign a stub code."""
    global _next_id
    code = f"STUB-{_next_id}"
    _next_id += 1
    unit = _make_unit(code, {**body, "suit": body.get("suit", {"code": suit, "name": suit, "icon": "memo_pencil"})})
    _units[code] = unit
    return {"id": code}


@app.get("/rest/api/unit/v2/{code}")
def get_unit(code: str) -> Dict[str, Any]:
    """Return a single unit by code."""
    if code not in _units:
        raise HTTPException(status_code=404, detail=f"Unit '{code}' not found")
    return _units[code]


@app.patch("/rest/api/unit/v2/update/{code}")
def patch_unit_update(code: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Update a unit by code (merge patch into stored unit)."""
    if code not in _units:
        raise HTTPException(status_code=404, detail=f"Unit '{code}' not found")
    unit = _units[code]
    for key, value in body.items():
        if key == "attributes" and isinstance(unit.get("attributes"), list):
            unit["attributes"] = value
        else:
            unit[key] = value
    return {"id": code}


def main() -> None:
    run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
