"""
ToolAgent — handles math/calculator queries and falls back to LLM.

Supports:
  - Direct expressions:    "100 + 250", "2 ** 10", "(5 + 3) * 2"
  - Natural language math: "What is 50 * 4?", "calculate 2 ** 10"
  - Word-based math:       "multiply 6 by 7", "add 3 and 5", "divide 100 by 4"
  - Chained operations:    "add 50 to the previous result"
"""

import re

from app.agents.base_agent import BaseAgent
from app.tools.registry import ToolRegistry


class ToolAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.registry = ToolRegistry()
        self._last_result: float | None = None

    # ── expression extraction ─────────────────────────────────────────────

    def _extract_math_expression(self, text: str) -> str | None:
        """
        Pull a math expression out of natural language.

        Examples:
          "What is 50 * 4?"     → "50 * 4"
          "calculate 2 ** 10"   → "2 ** 10"
          "(99 + 1) * 3"        → "(99 + 1) * 3"  (returned as-is)
        """
        # strip trailing punctuation
        text = text.strip().rstrip("?.!")

        # if the whole string looks like a pure math expression, use it directly
        pure = re.fullmatch(r'[\d\s\.\+\-\*\/\%\(\)]+', text)
        if pure:
            return text.strip()

        # try to find a sub-expression: starts at a digit or '('
        match = re.search(r'[\(\d][\d\s\.\+\-\*\/\%\(\)]+', text)
        if match:
            expr = match.group().strip()
            # only return if it actually contains an operator
            if re.search(r'[\+\-\*\/\%]', expr):
                return expr

        return None

    def _resolve_word_math(self, prompt_lower: str) -> str | None:
        """
        Handle plain-English math like:
          "multiply 6 by 7"   → 42
          "add 25 and 75"     → 100
          "subtract 3 from 10"→ 7
          "divide 100 by 4"   → 25
          "what is 3 times 9" → 27
        """
        numbers = re.findall(r'\d+(?:\.\d+)?', prompt_lower)
        if len(numbers) < 2:
            return None

        a, b = float(numbers[0]), float(numbers[1])

        if any(kw in prompt_lower for kw in ["multiply", "times", "product"]):
            result = a * b
        elif any(kw in prompt_lower for kw in ["divide", "divided by"]):
            if b == 0:
                return "Calculator Result: Error: division by zero"
            result = a / b
        elif any(kw in prompt_lower for kw in ["add", "sum", "plus", "total"]):
            result = a + b
        elif any(kw in prompt_lower for kw in ["subtract", "minus", "difference"]):
            # handle "subtract 3 from 10" → 10 - 3
            if "from" in prompt_lower:
                result = b - a
            else:
                result = a - b
        else:
            return None

        if isinstance(result, float) and result.is_integer():
            result = int(result)
        if isinstance(result, (int, float)):
            self._last_result = float(result)
        return f"Calculator Result: {result}"

    # ── chaining ─────────────────────────────────────────────────────────

    def _chain_operation(self, prompt_lower: str, last_result: float, value: float) -> str | None:
        """Handle chained math operations using the previous result."""
        ops = {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "times": lambda a, b: a * b,
            "divide": lambda a, b: a / b if b != 0 else "Error: division by zero",
        }
        for keyword, func in ops.items():
            if keyword in prompt_lower:
                result = func(last_result, value)
                if isinstance(result, float) and isinstance(result, float) and result == int(result):
                    result = int(result)
                if isinstance(result, (int, float)):
                    self._last_result = float(result)
                return f"Calculator Result: {result}"
        return None

    # ── main run ──────────────────────────────────────────────────────────

    def run(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        tool = self.registry.get_tool("calculator")

        # 1. Chained operation using previous result
        prev_keywords = ["previous result", "last result", "previous answer", "that result", "that answer"]
        if any(kw in prompt_lower for kw in prev_keywords):
            if self._last_result is not None:
                number_match = re.search(r'\d+(?:\.\d+)?', prompt)
                if number_match:
                    value = float(number_match.group())
                    chained = self._chain_operation(prompt_lower, self._last_result, value)
                    if chained:
                        return chained
            return "There is no previous result available."

        # 2. Word-based math (multiply, add, divide, subtract + two numbers)
        word_math = self._resolve_word_math(prompt_lower)
        if word_math:
            return word_math

        # 3. Extract math expression from natural language ("What is 50 * 4?")
        expr = self._extract_math_expression(prompt)
        if expr:
            try:
                result = tool.execute(expr)
                if isinstance(result, (int, float)):
                    self._last_result = float(result)
                return f"Calculator Result: {result}"
            except Exception as e:
                return f"Calculator error: {e}"

        # 4. Fallback to LLM for everything else
        return super().run(prompt)
