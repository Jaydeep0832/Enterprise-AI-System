"""
BaseAgent — simple LLM-backed agent.

Memory is managed at the LangGraph level via Redis nodes.
BaseAgent itself is stateless — it only wraps LLM calls.
"""

from app.services.llm_service import LLMService


class BaseAgent:

    def __init__(self):
        self.llm = LLMService()

    def run(self, prompt: str, history: list = None) -> str:
        if history:
            recent = history[-6:]
            context = "Previous conversation:\n" + "\n".join(
                f"{m['role']}: {m['content']}" for m in recent
            ) + "\n\n"
            prompt = f"{context}Question: {prompt}\nAnswer:"
        return self.llm.generate(prompt)
