"""
test_memory.py — Tests for per-session Redis memory.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_add_and_retrieve():
    """Messages added to a session can be retrieved."""
    from app.memory.redis_memory import RedisMemory

    session_id = f"test-{uuid.uuid4()}"
    mem = RedisMemory(session_id)
    mem.clear()

    mem.add("user", "Hello")
    mem.add("assistant", "Hi there")

    context = mem.get_context()
    assert len(context) == 2
    assert context[0]["role"] == "user"
    assert context[0]["content"] == "Hello"
    assert context[1]["role"] == "assistant"
    assert context[1]["content"] == "Hi there"

    mem.clear()


def test_sessions_are_isolated():
    """Two different sessions do not share memory."""
    from app.memory.redis_memory import RedisMemory

    session_a = f"session-a-{uuid.uuid4()}"
    session_b = f"session-b-{uuid.uuid4()}"

    mem_a = RedisMemory(session_a)
    mem_b = RedisMemory(session_b)
    mem_a.clear()
    mem_b.clear()

    mem_a.add("user", "Message only in A")

    assert len(mem_b.get_context()) == 0

    mem_a.clear()
    mem_b.clear()


def test_clear_removes_all_messages():
    """Clearing a session removes all messages."""
    from app.memory.redis_memory import RedisMemory

    session_id = f"test-clear-{uuid.uuid4()}"
    mem = RedisMemory(session_id)

    mem.add("user", "to be deleted")
    assert len(mem.get_context()) >= 1

    mem.clear()
    assert mem.get_context() == []


def test_history_api_returns_correct_session(client, session_id):
    """GET /history/{session_id} returns the right session's messages."""
    from app.memory.redis_memory import RedisMemory

    # seed some messages
    mem = RedisMemory(session_id)
    mem.clear()
    mem.add("user", "test question")
    mem.add("assistant", "test answer")

    response = client.get(f"/api/v1/history/{session_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == session_id
    assert data["count"] >= 2

    messages = data["messages"]
    assert any(m["role"] == "user" for m in messages)
    assert any(m["role"] == "assistant" for m in messages)

    mem.clear()


def test_history_clear_endpoint(client):
    """DELETE /history/{session_id} clears the session."""
    from app.memory.redis_memory import RedisMemory

    sid = f"clear-test-{uuid.uuid4()}"
    mem = RedisMemory(sid)
    mem.add("user", "temporary message")

    response = client.delete(f"/api/v1/history/{sid}")
    assert response.status_code == 200
    assert response.json()["status"] == "cleared"

    assert mem.get_context() == []
