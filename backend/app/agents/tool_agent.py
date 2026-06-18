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

    def _extract_last_result_from_history(self, history: list) -> float | None:
        """Extract the last numeric result from assistant history."""
        if not history:
            return None
        for msg in reversed(history):
            content = str(msg.get("content", ""))
            match = re.search(r'Calculator Result:\s*([0-9\.\-]+)', content)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
            if msg.get("role") == "assistant":
                numbers = re.findall(r'-?\d+(?:\.\d+)?', content)
                if numbers:
                    try:
                        return float(numbers[-1])
                    except ValueError:
                        pass
        return None

    def _chain_operation(self, prompt_lower: str, last_result: float, value: float) -> str | None:
        """Handle chained math operations using the previous result."""
        if any(kw in prompt_lower for kw in ["divide", "divided", "div", "/"]):
            if value == 0:
                return "Calculator Result: Error: division by zero"
            result = last_result / value
        elif any(kw in prompt_lower for kw in ["multiply", "mult", "times", "product", "*"]):
            result = last_result * value
        elif any(kw in prompt_lower for kw in ["subtract", "subtarct", "sub", "minus", "difference", "-"]):
            if "from" in prompt_lower:
                result = value - last_result
            else:
                result = last_result - value
        elif any(kw in prompt_lower for kw in ["add", "plus", "sum", "total", "+"]):
            result = last_result + value
        else:
            return None

        if isinstance(result, float) and result.is_integer():
            result = int(result)
        if isinstance(result, (int, float)):
            self._last_result = float(result)
        return f"Calculator Result: {result}"

    # ── main run ──────────────────────────────────────────────────────────

    def run(self, prompt: str, history: list = None) -> str:
        prompt_lower = prompt.lower()
        tool = self.registry.get_tool("calculator")

        # 0. Get last result from memory or history
        last_result = self._last_result
        if last_result is None and history:
            last_result = self._extract_last_result_from_history(history)

        # 1. Chained operation using previous result or pronouns ("it", "itt", "that", "this", "add it with 5", "add 5 to it")
        prev_keywords = [
            "previous result", "last result", "previous answer", "that result", "that answer",
            "it", "itt", "that", "this", "the result", "the answer", "to it", "with it", "from it"
        ]

        numbers_in_prompt = re.findall(r'\d+(?:\.\d+)?', prompt_lower)
        is_chained = any(kw in prompt_lower for kw in prev_keywords) or (
            len(numbers_in_prompt) == 1 and any(op in prompt_lower for op in ["add", "plus", "subtract", "subtarct", "minus", "multiply", "mult", "times", "divide", "div", "+", "-", "*", "/"])
        )

        if is_chained:
            if last_result is not None:
                if numbers_in_prompt:
                    value = float(numbers_in_prompt[0])
                    chained = self._chain_operation(prompt_lower, last_result, value)
                    if chained:
                        return chained
            elif any(kw in prompt_lower for kw in ["previous result", "last result", "previous answer"]):
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

        # 4. Fallback to LLM with history for context-aware generation
        return super().run(prompt, history=history)
