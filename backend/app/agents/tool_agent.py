import re

from app.agents.base_agent import BaseAgent
from app.tools.registry import ToolRegistry


class ToolAgent(BaseAgent):

    def __init__(self):

        super().__init__()

        self.registry = ToolRegistry()

    def get_last_calculator_result(self):

        messages = self.memory.get_context()

        print("MEMORY:", messages)

        for message in reversed(messages):

            content = message["content"]

            if "Calculator Result:" in content:

                try:
                    return float(
                        content.split(":")[1].strip()
                    )

                except Exception as e:

                    print(
                        "PARSE ERROR:",
                        e
                    )

        return None

    def run(self, prompt: str) -> str:

        prompt_lower = prompt.lower()

        if (
            "previous result" in prompt_lower
            or "last result" in prompt_lower
            or "previous answer" in prompt_lower
        ):

            last_result = (
                self.get_last_calculator_result()
            )

            if last_result is not None:

                number_match = re.search(
                    r"\d+",
                    prompt
                )

                if number_match:

                    value = float(
                        number_match.group()
                    )

                    if "add" in prompt_lower:

                        result = (
                            last_result + value
                        )

                        response = (
                            f"Calculator Result: {result}"
                        )

                        self.memory.add(
                            "assistant",
                            response
                        )

                        return response

                    if "subtract" in prompt_lower:

                        result = (
                            last_result - value
                        )

                        response = (
                            f"Calculator Result: {result}"
                        )

                        self.memory.add(
                            "assistant",
                            response
                        )

                        return response

                    if "multiply" in prompt_lower:

                        result = (
                            last_result * value
                        )

                        response = (
                            f"Calculator Result: {result}"
                        )

                        self.memory.add(
                            "assistant",
                            response
                        )

                        return response

                    if "divide" in prompt_lower:

                        result = (
                            last_result / value
                        )

                        response = (
                            f"Calculator Result: {result}"
                        )

                        self.memory.add(
                            "assistant",
                            response
                        )

                        return response

            return (
                "There is no previous result "
                "available."
            )

        math_keywords = [
            "+",
            "-",
            "*",
            "/"
        ]

        if any(
            op in prompt
            for op in math_keywords
        ):

            try:

                tool = self.registry.get_tool(
                    "calculator"
                )

                print(
                    "TOOL:",
                    tool
                )

                result = tool.execute(
                    prompt
                )

                response = (
                    f"Calculator Result: {result}"
                )

                self.memory.add(
                    "assistant",
                    response
                )

                return response

            except Exception as e:

                print(
                    "CALCULATOR ERROR:",
                    e
                )

                raise

        return super().run(prompt)

