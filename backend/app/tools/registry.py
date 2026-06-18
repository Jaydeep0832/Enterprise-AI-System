from app.tools.calculator_tool import CalculatorTool
from app.tools.web_search_tool import WebSearchTool


class ToolRegistry:

    def __init__(self):
        self.tools = {
            "calculator": CalculatorTool(),
            "web_search": WebSearchTool(),
        }

    def get_tool(self, name: str):
        return self.tools.get(name)

    def list_tools(self):
        return list(self.tools.keys())
