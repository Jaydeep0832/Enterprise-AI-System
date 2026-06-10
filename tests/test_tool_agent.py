"""
test_tool_agent.py — Tests for ToolAgent natural language math parsing.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def make_agent():
    from app.agents.tool_agent import ToolAgent
    return ToolAgent()


def test_direct_expression():
    """Plain math expression works."""
    agent = make_agent()
    result = agent.run("100 + 250")
    assert "350" in result


def test_natural_language_what_is():
    """'What is 50 * 4?' should NOT give an error."""
    agent = make_agent()
    result = agent.run("What is 50 * 4?")
    assert "200" in result
    assert "Invalid expression" not in result
    assert "syntax" not in result.lower()


def test_natural_language_calculate():
    """'calculate 2 ** 10' extracts the expression."""
    agent = make_agent()
    result = agent.run("calculate 2 ** 10")
    assert "1024" in result


def test_word_multiply():
    """'multiply 6 by 7' → 42."""
    agent = make_agent()
    result = agent.run("multiply 6 by 7")
    assert "42" in result


def test_word_add():
    """'add 25 and 75' → 100."""
    agent = make_agent()
    result = agent.run("add 25 and 75")
    assert "100" in result


def test_word_subtract():
    """'subtract 3 from 10' → 7."""
    agent = make_agent()
    result = agent.run("subtract 3 from 10")
    assert "7" in result


def test_word_divide():
    """'divide 100 by 4' → 25."""
    agent = make_agent()
    result = agent.run("divide 100 by 4")
    assert "25" in result


def test_chain_from_previous():
    """Chain operations use _last_result."""
    agent = make_agent()
    agent.run("50 * 4")  # sets _last_result = 200
    result = agent.run("add 100 to the previous result")
    assert "300" in result


def test_chain_multiply_previous():
    agent = make_agent()
    agent.run("50 * 4")  # 200
    agent.run("add 100 to the previous result")  # 300
    result = agent.run("multiply the last result by 2")
    assert "600" in result
