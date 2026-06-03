from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy import Integer
from sqlalchemy import Text


class Base(DeclarativeBase):
    pass


class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
