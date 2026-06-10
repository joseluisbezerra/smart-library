from types import SimpleNamespace
from uuid import uuid4

from datetime import (
    date,
    datetime,
    timezone
)

from unittest.mock import (
    ANY,
    Mock
)

from fastapi import status

from app.modules.books.controller import service
from app.modules.books.exceptions import BookProcessingRetryError
from app.modules.books.model import (
    BookType,
    ProcessingStatus
)


def make_book() -> SimpleNamespace:
    now = datetime.now(timezone.utc)

    return SimpleNamespace(
        id=uuid4(),
        title="Clean Code",
        author="Robert C. Martin",
        summary="Software craftsmanship book.",
        publication_date=date(2008, 8, 1),
        file_extension=".pdf",
        type=BookType.TECHNICAL,
        processing_attempts=0,
        processing_status=ProcessingStatus.QUEUED,
        created_at=now,
        updated_at=now,
    )


def test_list_books_calls_service(client, monkeypatch):
    list_books = Mock(return_value=[])
    monkeypatch.setattr(service, "list_books", list_books)

    response = client.get("/books", params={"title": "clean", "author": "martin"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
    list_books.assert_called_once_with(ANY, title="clean", author="martin")


def test_create_book_rejects_invalid_content_type(client, monkeypatch):
    create_book = Mock()
    monkeypatch.setattr(service, "create_book", create_book)

    response = client.post(
        "/books",
        data={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "summary": "Software craftsmanship book.",
            "publication_date": "2008-08-01",
            "type": BookType.TECHNICAL.value,
        },
        files={"file": ("book.txt", b"content", "text/plain")},
    )

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert response.json()["detail"] == "File must be PDF, JPEG, or PNG"
    create_book.assert_not_called()


def test_create_book_rejects_invalid_extension(client, monkeypatch):
    create_book = Mock()
    monkeypatch.setattr(service, "create_book", create_book)

    response = client.post(
        "/books",
        data={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "summary": "Software craftsmanship book.",
            "publication_date": "2008-08-01",
            "type": BookType.TECHNICAL.value,
        },
        files={"file": ("book.txt", b"content", "application/pdf")},
    )

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert response.json()["detail"] == "File extension must be PDF, JPEG, JPG, or PNG"
    create_book.assert_not_called()


def test_create_book_accepts_valid_upload(client, monkeypatch):
    book = make_book()
    create_book = Mock(return_value=book)
    monkeypatch.setattr(service, "create_book", create_book)

    response = client.post(
        "/books",
        data={
            "title": book.title,
            "author": book.author,
            "summary": book.summary,
            "publication_date": str(book.publication_date),
            "type": book.type.value,
        },
        files={"file": ("book.pdf", b"content", "application/pdf")},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["id"] == str(book.id)
    create_book.assert_called_once()


def test_retry_book_processing_returns_404_when_book_does_not_exist(client, monkeypatch):
    monkeypatch.setattr(service, "get_book", Mock(return_value=None))

    response = client.post(f"/books/{uuid4()}/retry-processing")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Book not found"


def test_retry_book_processing_returns_409_when_retry_is_invalid(client, monkeypatch):
    book = make_book()
    monkeypatch.setattr(service, "get_book", Mock(return_value=book))
    monkeypatch.setattr(
        service,
        "retry_book_processing",
        Mock(side_effect=BookProcessingRetryError("Book cannot be reprocessed")),
    )

    response = client.post(f"/books/{book.id}/retry-processing")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Book cannot be reprocessed"


def test_update_book_returns_404_when_book_does_not_exist(client, monkeypatch):
    monkeypatch.setattr(service, "get_book", Mock(return_value=None))

    response = client.put(f"/books/{uuid4()}", json={"title": "New title"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Book not found"


def test_delete_book_returns_204_when_book_exists(client, monkeypatch):
    book = make_book()
    delete_book = Mock()
    monkeypatch.setattr(service, "get_book", Mock(return_value=book))
    monkeypatch.setattr(service, "delete_book", delete_book)

    response = client.delete(f"/books/{book.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    delete_book.assert_called_once_with(ANY, book)
