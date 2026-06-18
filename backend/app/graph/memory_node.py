from app.memory.redis_memory import RedisMemory
from app.memory.long_term_memory import LongTermMemory


def load_memory_node(state):
    """Pull conversation history from Redis for the current session."""
    session_id = state.get("session_id", "default")
    user_id = session_id.split("-")[0] if "-" in session_id else session_id

    memory = RedisMemory(session_id)
    history = memory.get_context()
    
    ltm = LongTermMemory(user_id)
    context_str = ltm.get_context_string()
    
    if context_str:
        history.insert(0, {"role": "system", "content": context_str})

    return {"history": history}
