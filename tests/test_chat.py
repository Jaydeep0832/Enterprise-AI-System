"""
test_chat.py — Integration tests for the chat endpoint (LangGraph workflow).

Note: These tests make real LLM calls. Ensure at least one API key is set.
"""


def test_chat_returns_200(client, session_id):
    """Chat endpoint must return 200."""
    response = client.post(
        "/api/v1/chat",
        json={"question": "What is 5 + 3?", "session_id": session_id},
    )
    assert response.status_code == 200


def test_chat_response_structure(client, session_id):
    """Response must contain 'answer' and 'session_id'."""
    response = client.post(
        "/api/v1/chat",
        json={"question": "Hello, who are you?", "session_id": session_id},
    )
    data = response.json()
    assert "answer" in data
    assert "session_id" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0


def test_chat_returns_session_id(client):
    """When no session_id is given, the backend assigns one."""
    response = client.post(
        "/api/v1/chat",
        json={"question": "Generate a session for me"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0


def test_chat_math_routes_to_calculator(client, session_id):
    """Math expression should route to the tool agent and return a numeric result."""
    response = client.post(
        "/api/v1/chat",
        json={"question": "100 + 200", "session_id": session_id},
    )
    assert response.status_code == 200
    answer = response.json()["answer"]
    # Calculator result should appear somewhere in the answer
    assert "300" in answer or "Calculator" in answer


def test_chat_research_question(client, session_id):
    """General questions route to the research agent and return a real answer."""
    response = client.post(
        "/api/v1/chat",
        json={"question": "Explain what machine learning is", "session_id": session_id},
    )
    assert response.status_code == 200
    answer = response.json()["answer"]
    assert len(answer) > 50  # should be a proper response, not empty


def test_chat_session_consistency(client, session_id):
    """Same session_id returns the same session_id in the response."""
    response = client.post(
        "/api/v1/chat",
        json={"question": "Another question", "session_id": session_id},
    )
    assert response.json()["session_id"] == session_id


def test_rag_endpoint(client):
    """POST /rag endpoint answers a question using the RAG agent."""
    response = client.post(
        "/api/v1/rag",
        json={"question": "What documents have been uploaded?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)


def test_research_endpoint(client):
    """POST /research endpoint returns a research response."""
    response = client.post(
        "/api/v1/research",
        json={"topic": "Python programming language"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data or "answer" in data or "response" in data
