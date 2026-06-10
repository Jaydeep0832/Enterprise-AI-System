"""
ToolAgent — handles math/calculator queries and falls back to LLM.

Calculator memory chaining (e.g. "add 5 to previous result") uses the
session history passed in, rather than a module-level singleton.
"""

import re

from app.agents.base_agent import BaseAgent
from app.tools.registry import ToolRegistry


class ToolAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.registry = ToolRegistry()
        self._last_result: float | None = None

    def run(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        # check if user wants to operate on the previous result
        prev_keywords = ["previous result", "last result", "previous answer"]
        if any(kw in prompt_lower for kw in prev_keywords):
            if self._last_result is not None:
                number_match = re.search(r"[\d.]+", prompt)
                if number_match:
                    value = float(number_match.group())
                    chained = self._chain_operation(prompt_lower, self._last_result, value)
                    if chained:
                        return chained
            return "There is no previous result available."

        # check for direct math expressions
        if any(op in prompt for op in ["+", "-", "*", "/"]):
            try:
                tool = self.registry.get_tool("calculator")
                result = tool.execute(prompt)
                if isinstance(result, (int, float)):
                    self._last_result = float(result)
                return f"Calculator Result: {result}"
            except Exception as e:
                return f"Calculator error: {e}"

        # fallback to LLM
        return super().run(prompt)

    def _chain_operation(self, prompt_lower: str, last_result: float, value: float):
        """Handle chained math operations using the previous result."""
        ops = {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "divide": lambda a, b: a / b if b != 0 else "Error: division by zero",
        }

        for keyword, func in ops.items():
            if keyword in prompt_lower:
                result = func(last_result, value)
                if isinstance(result, (int, float)):
                    self._last_result = float(result)
                return f"Calculator Result: {result}"

        return None
