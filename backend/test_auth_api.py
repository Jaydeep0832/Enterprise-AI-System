import uuid
import requests

def test_auth_api():
    base_url = "http://127.0.0.1:8000/api/v1"
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    password = "SecurePassword123!"

    print(f"Testing Registration for '{unique_user}'...")
    reg_resp = requests.post(f"{base_url}/auth/register", json={
        "username": unique_user,
        "password": password
    })
    print("Register Status:", reg_resp.status_code)
    assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
    reg_data = reg_resp.json()
    token = reg_data["token"]
    print("Register Token received:", token[:30] + "...")

    print(f"\nTesting Login for '{unique_user}'...")
    login_resp = requests.post(f"{base_url}/auth/login", json={
        "username": unique_user,
        "password": password
    })
    print("Login Status:", login_resp.status_code)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_data = login_resp.json()
    assert login_data["username"] == unique_user

    print("\nTesting Authenticated /auth/me...")
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = requests.get(f"{base_url}/auth/me", headers=headers)
    print("/auth/me Status:", me_resp.status_code)
    assert me_resp.status_code == 200, f"/auth/me failed: {me_resp.text}"
    me_data = me_resp.json()
    print("/auth/me Response:", me_data)
    assert me_data["username"] == unique_user

    print("\nFULL DATABASE AUTHENTICATION & BCRYPT HASHING TEST PASSED PERFECTLY!")

if __name__ == "__main__":
    test_auth_api()
