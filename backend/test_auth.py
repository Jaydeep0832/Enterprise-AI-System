from app.core.auth import hash_password, verify_password, create_access_token, verify_token

def test_auth_hashing():
    pwd = "MySecretPassword123"
    hashed = hash_password(pwd)
    print("Hashed Password:", hashed)

    is_valid = verify_password(pwd, hashed)
    print("Password Verification:", is_valid)
    assert is_valid is True

    token = create_access_token(1, "testuser")
    print("JWT Token Generated:", token)

    payload = verify_token(token)
    print("Token Verified Payload:", payload)
    assert payload["username"] == "testuser"
    print("ALL AUTH FUNCTIONS WORKING PERFECTLY!")

if __name__ == "__main__":
    test_auth_hashing()
