import json
import time

from collections.abc import Iterator
from fastapi import UploadFile
from shutil import copyfileobj
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import (
    func,
    select
)

from app.modules.books.exceptions import BookProcessingRetryError
from app.core.utils import format_sse
from app.core.celery_app import celery

from app.modules.books.model import (
    Book,
    ProcessingStatus
)

from app.core.cache import (
    BOOKS_PROCESSING_PROGRESS_KEY,
    redis_client
)

from app.modules.books.schemas import (
    BookCreate,
    BookUpdate
)

FILE_STORAGE_PATH = Path("/shared")
MAX_PROCESSING_ATTEMPTS = 3


def create_book(db: Session, payload: BookCreate, file: UploadFile) -> Book:
    file_extension = Path(file.filename or "").suffix.lower()
    book = Book(**payload.model_dump(), file_extension=file_extension)

    try:
        db.add(book)
        db.flush()

        unique_file_name = f"{str(book.id)}{file_extension}"
        file_location = FILE_STORAGE_PATH / unique_file_name

        with open(file_location, "wb") as destination:
            copyfileobj(file.file, destination)

        db.commit()
        db.refresh(book)

        celery.send_task(
            "worker.book_processing_task",
            args=[unique_file_name, str(book.id)]
        )

        return book
    except Exception:
        db.rollback()

        raise


def list_books(
    db: Session,
    title: str | None = None,
    author: str | None = None,
) -> list[Book]:
    statement = select(Book).order_by(Book.created_at.desc())

    if title:
        statement = statement.where(
            func.unaccent(Book.title).ilike(func.unaccent(f"%{title}%"))
        )

    if author:
        statement = statement.where(
            func.unaccent(Book.author).ilike(func.unaccent(f"%{author}%"))
        )

    return list(db.scalars(statement).all())


def stream_books_processing_progress(interval: float = 2.0) -> Iterator[str]:
    yield "retry: 5000\n\n"

    while True:
        payload = []

        for cache_value in redis_client.hvals(BOOKS_PROCESSING_PROGRESS_KEY):
            try:
                payload.append(json.loads(cache_value))
            except json.JSONDecodeError:
                continue

        yield format_sse("books_processing_progress", payload)
        time.sleep(interval)


def get_book(db: Session, book_id: UUID) -> Book | None:
    return db.get(Book, book_id)


def retry_book_processing(db: Session, book: Book) -> Book:
    if book.processing_status != ProcessingStatus.PROCESSING_FAILED:
        raise BookProcessingRetryError("Book cannot be reprocessed")

    if book.processing_attempts >= MAX_PROCESSING_ATTEMPTS:
        raise BookProcessingRetryError("Maximum processing attempts reached")

    file_name = f"{book.id}{book.file_extension}"
    file_location = FILE_STORAGE_PATH / file_name

    if not file_location.exists():
        raise BookProcessingRetryError("Book file was not found")

    book.processing_attempts += 1
    book.processing_status = ProcessingStatus.QUEUED

    db.commit()
    db.refresh(book)

    celery.send_task(
        "worker.book_processing_task",
        args=[file_name, str(book.id)]
    )

    return book


def update_book(db: Session, book: Book, payload: BookUpdate) -> Book:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)

    return book


def delete_book(db: Session, book: Book) -> None:
    file_location = FILE_STORAGE_PATH / f"{book.id}{book.file_extension}"

    db.delete(book)
    db.commit()

    file_location.unlink(missing_ok=True)
