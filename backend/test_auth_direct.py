import uuid
from app.db.session import engine, SessionLocal
from app.models.document import Base
from app.models.user import User
from app.core.auth import hash_password, verify_password, create_access_token

def test_direct_db_auth():
    # Ensure all tables exist in PostgreSQL
    Base.metadata.create_all(bind=engine)
    print("Database tables ensured!")

    db = SessionLocal()
    try:
        username = f"db_user_{uuid.uuid4().hex[:6]}"
        raw_password = "MySecurePassword123!"

        # Hash password using bcrypt
        hashed = hash_password(raw_password)
        print(f"Bcrypt Hashed Password for '{username}': {hashed}")

        # Store in PostgreSQL users table
        user = User(username=username, password_hash=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User stored in DB with ID: {user.id}")

        # Retrieve user from PostgreSQL users table
        db_user = db.query(User).filter(User.username == username).first()
        assert db_user is not None
        assert db_user.username == username

        # Verify bcrypt hash against database stored hash
        is_pwd_valid = verify_password(raw_password, db_user.password_hash)
        print("Database Password Verification Result:", is_pwd_valid)
        assert is_pwd_valid is True

        # Generate JWT Token for database user
        token = create_access_token(db_user.id, db_user.username)
        print("Generated JWT Access Token:", token)

        print("\n✅ DIRECT POSTGRESQL DATABASE AUTHENTICATION & BCRYPT HASHING TEST PASSED!")
    finally:
        db.close()

if __name__ == "__main__":
    test_direct_db_auth()
