from pgvector.sqlalchemy import Vector
from enum import Enum

from datetime import (
    date,
    datetime
)

from uuid import (
    UUID,
    uuid4
)

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from core.database import Base


class ProcessingStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    PROCESSING_FAILED = "processing failed"


class BookType(str, Enum):
    COMMON = "common"
    TECHNICAL = "technical"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    publication_date: Mapped[date] = mapped_column(Date, nullable=False)

    type: Mapped[BookType] = mapped_column(
        SQLEnum(
            BookType,
            name="book_type",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(
            ProcessingStatus,
            name="processing_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    chunks: Mapped[list["BookChunk"]] = relationship(back_populates="book")


class BookChunk(Base):
    __tablename__ = "book_chunks"
    __table_args__ = (
        UniqueConstraint(
            "book_id",
            "chunk_index",
            name="uq_book_chunks_book_id_chunk_index",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    book_id: Mapped[UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    book: Mapped[Book] = relationship(back_populates="chunks")
