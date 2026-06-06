from app.memory.redis_memory import RedisMemory


def load_memory_node(state):
    """Pull conversation history from Redis for the current session."""
    session_id = state.get("session_id", "default")

    memory = RedisMemory(session_id)
    history = memory.get_context()

    return {"history": history}
