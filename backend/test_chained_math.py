import uuid
from app.graph.langgraph_workflow import graph

def test_full_chained_math_sequence():
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"

    # Step 1: 25+6 -> 31
    res1 = graph.invoke({"query": "25+6", "session_id": session_id})
    print("1. 25+6 ->", res1["result"])
    assert "31" in res1["result"]

    # Step 2: add it with 5 -> 36
    res2 = graph.invoke({"query": "add it with 5", "session_id": session_id})
    print("2. add it with 5 ->", res2["result"])
    assert "36" in res2["result"]

    # Step 3: divide it with 5 -> 7.2
    res3 = graph.invoke({"query": "divide it with 5", "session_id": session_id})
    print("3. divide it with 5 ->", res3["result"])
    assert "7.2" in res3["result"]

    # Step 4: multiply it with 5 -> 36
    res4 = graph.invoke({"query": "multiply it with 5", "session_id": session_id})
    print("4. multiply it with 5 ->", res4["result"])
    assert "36" in res4["result"]

    # Step 5: subtarct itt with 5 (with typos!) -> 31
    res5 = graph.invoke({"query": "subtarct itt with 5", "session_id": session_id})
    print("5. subtarct itt with 5 ->", res5["result"])
    assert "31" in res5["result"]

    print("ALL 5 CHAINED MATH OPERATIONS (ADD, DIVIDE, MULTIPLY, SUBTRACT + TYPOS) PASSED PERFECTLY!")

if __name__ == "__main__":
    test_full_chained_math_sequence()
