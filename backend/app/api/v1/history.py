"""
History API — per-session conversation history from Redis.

Routes:
  GET /history/{session_id}        — Get conversation history for a session
  DELETE /history/{session_id}     — Clear history for a session
"""

from fastapi import APIRouter

from app.memory.redis_memory import RedisMemory

router = APIRouter()


@router.get("/history/{session_id}")
def get_history(session_id: str):
    """Get the full conversation history for a session from Redis."""
    memory = RedisMemory(session_id)
    messages = memory.get_context()
    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }


@router.delete("/history/{session_id}")
def clear_history(session_id: str):
    """Clear conversation history for a session."""
    memory = RedisMemory(session_id)
    memory.clear()
    return {"status": "cleared", "session_id": session_id}
