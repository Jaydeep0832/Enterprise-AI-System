import re

from app.agents.base_agent import BaseAgent
from app.tools.registry import ToolRegistry


class ToolAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.registry = ToolRegistry()

    def get_last_calculator_result(self):
        messages = self.memory.get_context()
        for message in reversed(messages):
            content = message["content"]
            if "Calculator Result:" in content:
                try:
                    return float(content.split(":")[1].strip())
                except (ValueError, IndexError):
                    continue
        return None

    def _chain_operation(self, prompt_lower, last_result, value):
        """Handle chained math operations using the previous result."""
        ops = {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "divide": lambda a, b: a / b,
        }

        for keyword, func in ops.items():
            if keyword in prompt_lower:
                result = func(last_result, value)
                response = f"Calculator Result: {result}"
                self.memory.add("assistant", response)
                return response

        return None

    def run(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        # check if user wants to operate on the previous result
        prev_keywords = ["previous result", "last result", "previous answer"]
        if any(kw in prompt_lower for kw in prev_keywords):
            last_result = self.get_last_calculator_result()

            if last_result is not None:
                number_match = re.search(r"\d+", prompt)
                if number_match:
                    value = float(number_match.group())
                    chained = self._chain_operation(prompt_lower, last_result, value)
                    if chained:
                        return chained

            return "There is no previous result available."

        # check for direct math expressions
        if any(op in prompt for op in ["+", "-", "*", "/"]):
            try:
                tool = self.registry.get_tool("calculator")
                result = tool.execute(prompt)
                response = f"Calculator Result: {result}"
                self.memory.add("assistant", response)
                return response
            except Exception as e:
                print(f"Calculator error: {e}")
                raise

        # fallback to LLM
        return super().run(prompt)
