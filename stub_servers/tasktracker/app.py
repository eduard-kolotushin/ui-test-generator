"""TaskTracker REST API stub: folders (nested) and test cases."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="TaskTracker Stub", version="0.1.0")


class FolderCreate(BaseModel):
    name: str
    parent_id: str | None = None


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: str | None = None


class TestCaseCreate(BaseModel):
    folder: str
    name: str
    description: str = ""
    steps: list[str] = []


class TestCaseUpdate(BaseModel):
    folder: str | None = None
    name: str | None = None
    description: str | None = None
    steps: list[str] | None = None

# In-memory storage
_folders: list[dict[str, Any]] = []
_test_cases: list[dict[str, Any]] = []


# ---- Folder models and API ----

def _folder_dict(name: str, parent_id: str | None = None) -> dict[str, Any]:
    return {"id": f"folder-{uuid.uuid4().hex[:12]}", "name": name, "parent_id": parent_id}


@app.get("/folders")
def get_folders(parent_id: str | None = None) -> list[dict[str, Any]]:
    """List folders. No param: all. parent_id=: roots only. parent_id=<id>: children of that folder."""
    if parent_id is None:
        return list(_folders)
    if parent_id == "":
        return [f for f in _folders if f.get("parent_id") is None or f.get("parent_id") == ""]
    return [f for f in _folders if f.get("parent_id") == parent_id]


@app.get("/folders/{folder_id}")
def get_folder(folder_id: str) -> dict[str, Any]:
    folder = next((f for f in _folders if f["id"] == folder_id), None)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@app.post("/folders")
def create_folder(body: FolderCreate) -> dict[str, Any]:
    folder = _folder_dict(name=body.name, parent_id=body.parent_id)
    _folders.append(folder)
    return folder


@app.put("/folders/{folder_id}")
def update_folder(folder_id: str, body: FolderUpdate) -> dict[str, Any]:
    folder = next((f for f in _folders if f["id"] == folder_id), None)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if body.name is not None:
        folder["name"] = body.name
    if body.parent_id is not None:
        folder["parent_id"] = body.parent_id
    return folder


@app.delete("/folders/{folder_id}")
def delete_folder(folder_id: str) -> None:
    folder = next((f for f in _folders if f["id"] == folder_id), None)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    _folders.remove(folder)
    # Optionally delete test cases in this folder
    global _test_cases
    _test_cases = [tc for tc in _test_cases if tc.get("folder") != folder_id]


# ---- Test case models and API ----
# Test case: folder (str), name (str), description (str), steps (list[str])


@app.get("/test-cases")
def get_test_cases(folder: str | None = None) -> list[dict[str, Any]]:
    """List test cases. Optional query 'folder' to filter by folder id."""
    if folder is None:
        return list(_test_cases)
    return [dict(tc) for tc in _test_cases if tc.get("folder") == folder]


@app.get("/test-cases/{test_case_id}")
def get_test_case(test_case_id: str) -> dict[str, Any]:
    tc = next((t for t in _test_cases if t["id"] == test_case_id), None)
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    return tc


@app.post("/test-cases")
def create_test_case(body: TestCaseCreate) -> dict[str, Any]:
    tc = {
        "id": f"tc-{uuid.uuid4().hex[:12]}",
        "folder": body.folder,
        "name": body.name,
        "description": body.description,
        "steps": list(body.steps),
    }
    _test_cases.append(tc)
    return tc


@app.put("/test-cases/{test_case_id}")
def update_test_case(test_case_id: str, body: TestCaseUpdate) -> dict[str, Any]:
    tc = next((t for t in _test_cases if t["id"] == test_case_id), None)
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    if body.folder is not None:
        tc["folder"] = body.folder
    if body.name is not None:
        tc["name"] = body.name
    if body.description is not None:
        tc["description"] = body.description
    if body.steps is not None:
        tc["steps"] = body.steps
    return tc


@app.delete("/test-cases/{test_case_id}")
def delete_test_case(test_case_id: str) -> None:
    tc = next((t for t in _test_cases if t["id"] == test_case_id), None)
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    _test_cases.remove(tc)
