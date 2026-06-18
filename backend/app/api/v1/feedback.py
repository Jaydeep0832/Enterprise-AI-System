"""
Feedback API — human feedback on AI responses.

Routes:
  POST /feedback               — Submit thumbs up/down feedback
  GET  /feedback               — List all feedback
  GET  /feedback/stats         — Aggregate feedback statistics
  GET  /feedback/analysis      — Analyze negative feedback patterns
  GET  /feedback/suggestions   — Get LLM-generated prompt improvements
"""

from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.db.session import SessionLocal, engine
from app.models.feedback import Feedback
from app.evaluation.prompt_optimizer import analyze_negative_feedback, generate_prompt_suggestions
from sqlalchemy import text

router = APIRouter()


class FeedbackRequest(BaseModel):
    session_id: str
    message_index: int
    rating: int  # 1 = thumbs up, -1 = thumbs down
    comment: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on an AI response."""
    if request.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 (thumbs up) or -1 (thumbs down)")

    db = SessionLocal()
    try:
        fb = Feedback(
            session_id=request.session_id,
            message_index=request.message_index,
            rating=request.rating,
            comment=request.comment,
        )
        db.add(fb)
        db.commit()
        return {"status": "recorded", "id": fb.id}
    finally:
        db.close()


@router.get("/feedback")
async def list_feedback(limit: int = 50, offset: int = 0):
    """List all feedback entries."""
    sql = text("""
        SELECT id, session_id, message_index, rating, comment, created_at
        FROM feedback
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    count_sql = text("SELECT COUNT(*) FROM feedback")

    with engine.begin() as conn:
        rows = conn.execute(sql, {"limit": limit, "offset": offset}).fetchall()
        total = conn.execute(count_sql).scalar()

    return {
        "feedback": [
            {
                "id": r.id, "session_id": r.session_id,
                "message_index": r.message_index, "rating": r.rating,
                "comment": r.comment, "created_at": str(r.created_at),
            }
            for r in rows
        ],
        "total": total,
    }


@router.get("/feedback/stats")
async def feedback_stats():
    """Get aggregate feedback statistics."""
    sql = text("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE rating = 1) AS positive,
            COUNT(*) FILTER (WHERE rating = -1) AS negative
        FROM feedback
    """)

    with engine.begin() as conn:
        row = conn.execute(sql).fetchone()

    total = row.total or 0
    positive = row.positive or 0
    negative = row.negative or 0

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_rate": round(positive / max(total, 1) * 100, 1),
        "negative_rate": round(negative / max(total, 1) * 100, 1),
    }


@router.get("/feedback/analysis")
async def get_feedback_analysis():
    """Analyze negative feedback patterns using LLM."""
    return analyze_negative_feedback()


@router.get("/feedback/suggestions")
async def get_prompt_suggestions():
    """Get LLM-generated prompt improvement suggestions based on negative feedback."""
    return generate_prompt_suggestions()
