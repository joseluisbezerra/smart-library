import pytesseract

from langchain_text_splitters import RecursiveCharacterTextSplitter
from collections.abc import Iterable
from pathlib import Path
from uuid import UUID
from PIL import Image

from pdf2image import (
    convert_from_path,
    pdfinfo_from_path
)

from sqlalchemy import (
    delete,
    func,
    select
)

from core.database import get_session
from core.config import get_settings
from models import (
    Book,
    BookChunk,
    BookType,
    ProcessingStatus
)

settings = get_settings()
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def build_text_splitter(book_type: BookType) -> RecursiveCharacterTextSplitter:
    if book_type == BookType.TECHNICAL:
        return RecursiveCharacterTextSplitter(chunk_size=3500, chunk_overlap=500)

    return RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=250)


def calculate_progress(processed_pages: int, total_pages: int) -> float:
    if total_pages == 0:
        return 100.0

    return min((processed_pages / total_pages) * 100, 100.0)


def existing_processed_pages(chunks: Iterable[BookChunk]) -> set[int]:
    processed_pages: set[int] = set()

    for chunk in chunks:
        processed_pages.update(range(chunk.page_start, chunk.page_end + 1))

    return processed_pages


def get_total_pages(file_path: Path) -> int:
    if file_path.suffix.lower() == ".pdf":
        info = pdfinfo_from_path(file_path)

        return int(info["Pages"])

    return 1


def extract_page_text(file_path: Path, page_number: int) -> str:
    if file_path.suffix.lower() == ".pdf":
        images = convert_from_path(
            file_path,
            first_page=page_number,
            last_page=page_number,
        )

        if not images:
            return ""

        image = images[0]
    else:
        image = Image.open(file_path)

    return pytesseract.image_to_string(image, lang="por").strip()


def set_book_status(book: Book, status: ProcessingStatus) -> None:
    if book.processing_status != status:
        book.processing_status = status


def save_page_chunks(
    book_id: UUID,
    page_number: int,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    with get_session() as db:
        next_chunk_index = db.scalar(
            select(func.max(BookChunk.chunk_index)).where(BookChunk.book_id == book_id)
        )

        next_chunk_index = 0 if next_chunk_index is None else next_chunk_index + 1

        db.execute(
            delete(BookChunk).where(
                BookChunk.book_id == book_id,
                BookChunk.page_start == page_number,
                BookChunk.page_end == page_number,
            )
        )

        for content, embedding in zip(chunks, embeddings, strict=True):
            db.add(
                BookChunk(
                    book_id=book_id,
                    content=content,
                    embedding=embedding,
                    embedding_model=settings.openai_embedding_model,
                    chunk_index=next_chunk_index,
                    page_start=page_number,
                    page_end=page_number,
                )
            )

            next_chunk_index += 1
