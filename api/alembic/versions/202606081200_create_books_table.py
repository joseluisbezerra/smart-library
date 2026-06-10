"""create books table

Revision ID: 202606081200
Revises:
Create Date: 2026-06-08 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202606081200"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    book_type = postgresql.ENUM(
        "common",
        "technical",
        name="book_type",
        create_type=False,
    )

    book_type.create(op.get_bind(), checkfirst=True)

    processing_status = postgresql.ENUM(
        "queued",
        "processing",
        "processed",
        "processing failed",
        name="processing_status",
        create_type=False,
    )

    processing_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "books",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("file_extension", sa.String(), nullable=False),
        sa.Column("processing_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("type", book_type, nullable=False),
        sa.Column(
            "processing_status",
            processing_status,
            server_default="queued",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_books")),
    )
    op.create_index(op.f("ix_books_author"), "books", ["author"], unique=False)
    op.create_index(op.f("ix_books_id"), "books", ["id"], unique=False)
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)

    op.create_table(
        "book_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "embedding_model",
            sa.String(),
            server_default="text-embedding-3-small",
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_book_chunks")),
        sa.UniqueConstraint(
            "book_id",
            "chunk_index",
            name="uq_book_chunks_book_id_chunk_index",
        ),
    )
    op.create_index(op.f("ix_book_chunks_book_id"), "book_chunks", ["book_id"], unique=False)
    op.create_index(op.f("ix_book_chunks_id"), "book_chunks", ["id"], unique=False)
    op.execute(
        "CREATE INDEX ix_book_chunks_embedding "
        "ON book_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    book_type = postgresql.ENUM(
        "common",
        "technical",
        name="book_type",
        create_type=False,
    )
    processing_status = postgresql.ENUM(
        "queued",
        "processing",
        "processed",
        "processing failed",
        name="processing_status",
        create_type=False,
    )

    op.drop_index(op.f("ix_book_chunks_id"), table_name="book_chunks")
    op.drop_index(op.f("ix_book_chunks_book_id"), table_name="book_chunks")
    op.drop_index("ix_book_chunks_embedding", table_name="book_chunks")
    op.drop_table("book_chunks")
    op.drop_index(op.f("ix_books_title"), table_name="books")
    op.drop_index(op.f("ix_books_id"), table_name="books")
    op.drop_index(op.f("ix_books_author"), table_name="books")
    op.drop_table("books")
    processing_status.drop(op.get_bind(), checkfirst=True)
    book_type.drop(op.get_bind(), checkfirst=True)
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS unaccent")
