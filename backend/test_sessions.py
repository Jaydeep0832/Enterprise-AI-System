from app.memory.redis_memory import RedisMemory

user1 = RedisMemory(
    "user_1"
)

user2 = RedisMemory(
    "user_2"
)

user1.clear()
user2.clear()

user1.add(
    "user",
    "Hello from user1"
)

user2.add(
    "user",
    "Hello from user2"
)

print(
    user1.get_context()
)

print(
    user2.get_context()
)
