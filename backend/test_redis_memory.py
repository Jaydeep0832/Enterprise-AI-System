from app.memory.redis_memory import RedisMemory

memory = RedisMemory()

memory.clear()

memory.add(
    "user",
    "What is Redis?"
)

memory.add(
    "assistant",
    "Redis is an in-memory datastore."
)

print(
    memory.get_context()
)
