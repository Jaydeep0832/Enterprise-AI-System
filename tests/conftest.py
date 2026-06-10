"""
conftest.py — shared fixtures for the Enterprise AI System test suite.

Sets PYTHONPATH so tests can import from backend/app.
Loads .env from backend/ before importing any app modules.
"""

import os
import sys

import pytest

# 1. make 'app' importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# 2. load backend .env before any app module is imported
_env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
if os.path.exists(_env_path):
    from dotenv import load_dotenv
    load_dotenv(_env_path, override=True)


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient reused across the whole test session."""
    from app.main import app
    from starlette.testclient import TestClient
    return TestClient(app)


@pytest.fixture(scope="session")
def session_id():
    """Stable session ID used across chat/history tests."""
    return "test-session-phase6"
