from types import SimpleNamespace
from uuid import uuid4

from app.modules.books import service


class FakeSession:
    def __init__(self) -> None:
        self.deleted = None
        self.committed = False

    def delete(self, obj) -> None:
        self.deleted = obj

    def commit(self) -> None:
        self.committed = True


def test_delete_book_removes_record_and_storage_file(tmp_path, monkeypatch):
    book = SimpleNamespace(id=uuid4(), file_extension=".pdf")
    file_location = tmp_path / f"{book.id}{book.file_extension}"
    file_location.write_bytes(b"content")
    db = FakeSession()

    monkeypatch.setattr(service, "FILE_STORAGE_PATH", tmp_path)

    service.delete_book(db, book)

    assert db.deleted is book
    assert db.committed is True
    assert not file_location.exists()
