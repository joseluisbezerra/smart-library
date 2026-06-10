from datetime import date
from pathlib import Path as FilePath
from typing import Annotated
from uuid import UUID

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Response,
    UploadFile,
    status
)

from app.modules.books.exceptions import BookProcessingRetryError
from app.modules.books.model import BookType
from app.modules.books import service
from app.core.database import get_db
from app.modules.books.schemas import (
    BookCreate,
    BookRead,
    BookUpdate
)

router = APIRouter(prefix="/books", tags=["books"])

ALLOWED_BOOK_FILE_TYPES = {"application/pdf", "image/jpeg", "image/png"}
ALLOWED_BOOK_FILE_EXTENSIONS = {".pdf", ".jpeg", ".jpg", ".png"}


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create book",
    description=(
        "Creates a book record and stores the uploaded source file in `/shared` "
        "using the generated book UUID as the file name. Accepted files are PDF, JPEG, and PNG."
    ),
    responses={
        status.HTTP_201_CREATED: {"description": "Book created successfully."},
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "description": "Uploaded file is not PDF, JPEG, or PNG."
        },
    },
)
def create_book(
    title: Annotated[str, Form(description="Book title.")],
    author: Annotated[str, Form(description="Book author name.")],
    summary: Annotated[str, Form(description="Brief book summary.")],
    publication_date: Annotated[date, Form(description="Book publication date.")],
    type: Annotated[BookType, Form(description="Book type: common or technical.")],
    file: Annotated[UploadFile, File(description="Book source file in PDF, JPEG, or PNG format.")],
    db: Session = Depends(get_db),
) -> BookRead:
    if file.content_type not in ALLOWED_BOOK_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File must be PDF, JPEG, or PNG",
        )

    if not file.filename or FilePath(file.filename).suffix.lower() not in ALLOWED_BOOK_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File extension must be PDF, JPEG, JPG, or PNG",
        )

    payload = BookCreate(
        title=title,
        author=author,
        summary=summary,
        publication_date=publication_date,
        type=type,
    )

    return service.create_book(db, payload, file)


@router.get(
    "",
    response_model=list[BookRead],
    summary="List books",
    description=(
        "Lists books ordered by creation. Optional title and author filters are "
        "case-insensitive and accent-insensitive."
    ),
)
def list_books(
    title: Annotated[
        str | None,
        Query(description="Optional partial title filter."),
    ] = None,
    author: Annotated[
        str | None,
        Query(description="Optional partial author filter."),
    ] = None,
    db: Session = Depends(get_db),
) -> list[BookRead]:
    return service.list_books(db, title=title, author=author)


@router.get(
    "/processing-progress/stream",
    summary="Stream books processing progress",
    description=(
        "Streams processing progress for all books using Server-Sent Events. "
        "Each event contains a snapshot with every book and its current progress."
    ),
    response_class=StreamingResponse,
)
def stream_books_processing_progress(
    interval: Annotated[
        float,
        Query(
            ge=0.5,
            le=60,
            description="Seconds between progress snapshots.",
        ),
    ] = 2.0,
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_books_processing_progress(interval=interval),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{book_id}/retry-processing",
    response_model=BookRead,
    summary="Retry book processing",
    description="Retries processing a failed book. A book can be retried up to 3 times.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Book not found."},
        status.HTTP_409_CONFLICT: {"description": "Book cannot be reprocessed."},
    },
)
def retry_book_processing(
    book_id: Annotated[UUID, Path(description="Book UUID.")],
    db: Session = Depends(get_db),
) -> BookRead:
    book = service.get_book(db, book_id)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    try:
        return service.retry_book_processing(db, book)
    except BookProcessingRetryError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.put(
    "/{book_id}",
    response_model=BookRead,
    summary="Update book",
    description=(
        "Updates editable book metadata. The book type cannot be changed after creation."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Book not found."},
    },
)
def update_book(
    book_id: Annotated[UUID, Path(description="Book UUID.")],
    payload: Annotated[BookUpdate, Body(description="Editable book fields.")],
    db: Session = Depends(get_db),
) -> BookRead:
    book = service.get_book(db, book_id)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    return service.update_book(db, book, payload)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book",
    description="Deletes a book record and its related chunks.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Book deleted successfully."},
        status.HTTP_404_NOT_FOUND: {"description": "Book not found."},
    },
)
def delete_book(
    book_id: Annotated[UUID, Path(description="Book UUID.")],
    db: Session = Depends(get_db),
) -> Response:
    book = service.get_book(db, book_id)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    service.delete_book(db, book)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
