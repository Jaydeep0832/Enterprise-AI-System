from app.tools.base_tool import BaseTool


class CalculatorTool(BaseTool):

    def execute(self, expression: str):
        return eval(expression)
