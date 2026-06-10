import logging

from langchain_openai import OpenAIEmbeddings
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from core.cache import (
    redis_client,
    set_book_processing_cache
)

from core.celery_app import celery
from core.config import get_settings
from core.database import get_session

from models import (
    Book,
    BookChunk,
    ProcessingStatus
)

from utils import (
    build_text_splitter,
    calculate_progress,
    existing_processed_pages,
    extract_page_text,
    get_total_pages,
    save_page_chunks,
    set_book_status,
)


settings = get_settings()
DATA_DIR = Path("/shared")

logger = logging.getLogger("worker")


@celery.task(name="worker.book_processing_task")
def book_processing_task(file_name: str, book_id: str) -> dict[str, str | float]:
    parsed_book_id = UUID(book_id)
    progress = 0.0

    lock = redis_client.lock(
        f"{parsed_book_id}:lock",
        blocking_timeout=0
    )

    if not lock.acquire():
        logger.info("Book processing already running for book_id=%s", parsed_book_id)

        return {"status": ProcessingStatus.PROCESSING, "progress": progress}

    try:
        with get_session() as db:
            book = db.get(Book, parsed_book_id)

            if book is None:
                logger.warning("Book not found for processing: %s", parsed_book_id)

                return {"status": "not found", "progress": 0.0}

            if book.processing_status == ProcessingStatus.PROCESSED:
                set_book_processing_cache(parsed_book_id, ProcessingStatus.PROCESSED, 100.0)

                return {"status": ProcessingStatus.PROCESSED, "progress": 100.0}

            set_book_status(book, ProcessingStatus.PROCESSING)
            book_type = book.type

            file_path = DATA_DIR / file_name

            if not file_path.exists():
                raise FileNotFoundError(f"Book file not found: {file_path}")

            chunks = list(
                db.scalars(
                    select(BookChunk).where(BookChunk.book_id == parsed_book_id)
                )
            )

            total_pages = get_total_pages(file_path)
            processed_pages = existing_processed_pages(chunks)
            progress = calculate_progress(len(processed_pages), total_pages)
            set_book_processing_cache(parsed_book_id, ProcessingStatus.PROCESSING, progress)

            if progress == 100.0:
                set_book_status(book, ProcessingStatus.PROCESSED)
                set_book_processing_cache(parsed_book_id, ProcessingStatus.PROCESSED, 100.0)

                return {"status": ProcessingStatus.PROCESSED, "progress": 100.0}

        logger.info("Processing started for book_id=%s", parsed_book_id)

        embeddings = OpenAIEmbeddings(model=settings.openai_embedding_model)
        text_splitter = build_text_splitter(book_type)

        for page_number in range(1, total_pages + 1):
            if page_number in processed_pages:
                continue

            page_text = extract_page_text(file_path, page_number)
            page_chunks = [chunk for chunk in text_splitter.split_text(page_text) if chunk.strip()]

            if page_chunks:
                page_embeddings = embeddings.embed_documents(page_chunks)
                save_page_chunks(parsed_book_id, page_number, page_chunks, page_embeddings)

            processed_pages.add(page_number)
            progress = calculate_progress(len(processed_pages), total_pages)
            set_book_processing_cache(parsed_book_id, ProcessingStatus.PROCESSING, progress)

        with get_session() as db:
            book = db.get(Book, parsed_book_id)

            if book is None:
                logger.warning("Book was deleted during processing: %s", parsed_book_id)

                return {"status": "not found", "progress": progress}

            set_book_status(book, ProcessingStatus.PROCESSED)

        set_book_processing_cache(parsed_book_id, ProcessingStatus.PROCESSED, 100.0)

        logger.info("Processing completed for book_id=%s", parsed_book_id)

        return {"status": ProcessingStatus.PROCESSED, "progress": 100.0}
    except Exception as error:
        logger.exception("Error while processing book_id=%s", parsed_book_id)

        with get_session() as db:
            book = db.get(Book, parsed_book_id)

            if book is not None:
                set_book_status(book, ProcessingStatus.PROCESSING_FAILED)

        set_book_processing_cache(
            parsed_book_id,
            ProcessingStatus.PROCESSING_FAILED,
            progress,
            error=str(error),
        )

        raise
    finally:
        try:
            lock.release()
        except Exception:
            logger.warning("Could not release processing lock for book_id=%s", parsed_book_id)
