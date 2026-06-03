from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine
from app.db.redis_client import redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    db_status = "disconnected"
    redis_status = "disconnected"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass

    try:
        redis_client.ping()
        redis_status = "connected"
    except Exception:
        pass

    return {
        "status": "healthy",
        "database": db_status,
        "redis": redis_status,
        "service": "enterprise-ai-system"
    }
