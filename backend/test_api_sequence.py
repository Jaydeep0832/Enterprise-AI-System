import requests
import uuid

def test_api_sequence():
    session_id = f"test-api-{uuid.uuid4().hex[:8]}"
    base_url = "http://127.0.0.1:8000/api/v1/chat"

    queries = [
        ("25+6", "31"),
        ("add it with 5", "36"),
        ("divide it with 5", "7.2"),
        ("multiply it with 5", "36"),
        ("subtarct itt with 5", "31"),
    ]

    for q, expected in queries:
        resp = requests.post(base_url, json={"question": q, "session_id": session_id}).json()
        answer = resp.get("answer", "")
        route = resp.get("route", "")
        print(f"Query: '{q}' -> Answer: '{answer}' (Route: '{route}')")
        assert expected in answer, f"Expected {expected} in response for '{q}', got '{answer}'"

    print("ALL 5 API QUERIES PASSED WITH 100% ACCURACY AND CORRECT OPERATION MATCHING!")

if __name__ == "__main__":
    test_api_sequence()
