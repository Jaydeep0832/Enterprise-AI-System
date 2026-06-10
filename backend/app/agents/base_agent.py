"""
BaseAgent — simple LLM-backed agent.

Memory is managed at the LangGraph level via Redis nodes.
BaseAgent itself is stateless — it only wraps LLM calls.
"""

from app.services.llm_service import LLMService


class BaseAgent:

    def __init__(self):
        self.llm = LLMService()

    def run(self, prompt: str) -> str:
        return self.llm.generate(prompt)
