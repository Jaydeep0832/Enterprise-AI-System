from app.services.llm_service import LLMService
from app.memory.conversation_memory import memory


class BaseAgent:

    def __init__(self):
        self.llm = LLMService()
        self.memory = memory

    def run(self, prompt: str) -> str:
        self.memory.add("user", prompt)
        response = self.llm.generate(prompt)
        self.memory.add("assistant", response)
        return response
