"""
Evaluation models — stores RAG evaluation runs and results in PostgreSQL.
"""

from datetime import datetime

from sqlalchemy import Integer, String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.document import Base


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_size: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_faithfulness: Mapped[float] = mapped_column(Float, nullable=False)
    avg_relevancy: Mapped[float] = mapped_column(Float, nullable=False)
    avg_precision: Mapped[float] = mapped_column(Float, nullable=False)
    avg_overall: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    eval_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_preview: Mapped[str] = mapped_column(Text, nullable=True)
    faithfulness: Mapped[float] = mapped_column(Float, nullable=False)
    answer_relevancy: Mapped[float] = mapped_column(Float, nullable=False)
    context_precision: Mapped[float] = mapped_column(Float, nullable=False)
    hallucination: Mapped[float] = mapped_column(Float, nullable=True)
    context_recall: Mapped[float] = mapped_column(Float, nullable=True)
    overall: Mapped[float] = mapped_column(Float, nullable=False)
    num_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
