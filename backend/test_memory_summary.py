from app.memory.redis_memory import RedisMemory
from app.memory.memory_summarizer import MemorySummarizer

memory = RedisMemory("user_1")

summarizer = MemorySummarizer()

summary = summarizer.summarize(
    memory.get_context()
)

print(summary)
