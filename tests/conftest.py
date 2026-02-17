"""Pytest fixtures: use TaskTracker stub for all tests."""
import pytest

from src.tasktracker.client import set_client
from src.tasktracker.stub import TaskTrackerStubClient


@pytest.fixture(autouse=True)
def tasktracker_stub():
    """Inject a fresh in-memory stub as the TaskTracker client for every test."""
    stub = TaskTrackerStubClient()
    set_client(stub)
    yield stub
    set_client(None)
