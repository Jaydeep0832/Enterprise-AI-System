from app.memory.redis_memory import RedisMemory


def save_memory_node(state):
    """Save the current Q&A pair to Redis for future context."""
    session_id = state.get("session_id", "default")

    memory = RedisMemory(session_id)
    memory.add("user", state["query"])
    memory.add("assistant", state["result"])

    return state
