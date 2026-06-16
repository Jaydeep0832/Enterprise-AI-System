"""
Auth API — user registration and login.

Routes:
  POST /auth/register  — Create a new account
  POST /auth/login     — Get a JWT token
  GET  /auth/me        — Get current user info
"""

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends

from app.core.auth import hash_password, verify_password, create_access_token, require_auth
from app.db.session import SessionLocal
from app.models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str


@router.post("/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Create a new user account."""
    if len(request.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == request.username).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")

        user = User(
            username=request.username,
            password_hash=hash_password(request.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(user.id, user.username)
        return AuthResponse(token=token, username=user.username)
    finally:
        db.close()


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Authenticate and get a JWT token."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == request.username).first()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        token = create_access_token(user.id, user.username)
        return AuthResponse(token=token, username=user.username)
    finally:
        db.close()


@router.get("/auth/me")
async def get_me(user: dict = Depends(require_auth)):
    """Get the current authenticated user's info."""
    return {
        "user_id": user["sub"],
        "username": user["username"],
    }
