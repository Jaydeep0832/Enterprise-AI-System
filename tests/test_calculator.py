"""
test_calculator.py — Unit tests for the safe AST-based calculator tool.

Tests:
  - Basic arithmetic
  - Operator precedence
  - Negative numbers
  - Exponentiation and modulo
  - Division by zero (graceful error)
  - Security: blocked expressions
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.tools.calculator_tool import CalculatorTool


def test_addition():
    tool = CalculatorTool()
    assert tool.execute("2 + 3") == 5


def test_subtraction():
    tool = CalculatorTool()
    assert tool.execute("10 - 4") == 6


def test_multiplication():
    tool = CalculatorTool()
    assert tool.execute("3 * 7") == 21


def test_division():
    tool = CalculatorTool()
    assert tool.execute("15 / 4") == 3.75


def test_exponentiation():
    tool = CalculatorTool()
    assert tool.execute("2 ** 8") == 256


def test_modulo():
    tool = CalculatorTool()
    assert tool.execute("17 % 5") == 2


def test_complex_expression():
    tool = CalculatorTool()
    result = tool.execute("(10 + 5) * 2 - 3")
    assert result == 27


def test_negative_number():
    tool = CalculatorTool()
    assert tool.execute("-42") == -42


def test_float_arithmetic():
    tool = CalculatorTool()
    result = tool.execute("1.5 + 2.5")
    assert abs(result - 4.0) < 1e-9


def test_division_by_zero():
    tool = CalculatorTool()
    result = tool.execute("1 / 0")
    assert "Error" in str(result) or "division" in str(result).lower()


def test_security_import_blocked():
    """Ensure __import__ calls are rejected."""
    tool = CalculatorTool()
    result = tool.execute("__import__('os').system('ls')")
    assert "Invalid" in str(result) or "Unsupported" in str(result)


def test_security_function_call_blocked():
    """Ensure arbitrary function calls are rejected."""
    tool = CalculatorTool()
    result = tool.execute("open('/etc/passwd').read()")
    assert "Invalid" in str(result) or "Unsupported" in str(result)


def test_security_attribute_access_blocked():
    """Ensure attribute access is rejected."""
    tool = CalculatorTool()
    result = tool.execute("(1).__class__.__bases__")
    assert "Invalid" in str(result) or "Unsupported" in str(result)
