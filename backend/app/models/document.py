from datetime import datetime

from sqlalchemy import Integer, Text, String, DateTime, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(384))
    
    # Hybrid search vector
    search_vector = mapped_column(TSVECTOR)

    # metadata
    filename: Mapped[str] = mapped_column(String(512), nullable=False, default="unknown")
    file_type: Mapped[str] = mapped_column(String(32), nullable=False, default="pdf")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
