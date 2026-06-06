import ast
import operator

from app.tools.base_tool import BaseTool


class CalculatorTool(BaseTool):
    """Safe math expression evaluator using AST parsing.
    
    Only allows basic arithmetic: +, -, *, /, ** and unary negation.
    No function calls, imports, or attribute access allowed.
    """

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }

    UNARY_OPS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def execute(self, expression: str):
        expression = expression.strip()
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._eval_node(tree.body)
            return result
        except (ValueError, TypeError, SyntaxError) as e:
            return f"Invalid expression: {e}"
        except ZeroDivisionError:
            return "Error: division by zero"

    def _eval_node(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.OPERATORS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self.UNARY_OPS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            operand = self._eval_node(node.operand)
            return self.UNARY_OPS[op_type](operand)

        raise ValueError(
            f"Unsupported expression type: {type(node).__name__}. "
            "Only numbers and basic math operators are allowed."
        )
