import json

from uuid import UUID
from redis import Redis

from core.config import get_settings

settings = get_settings()
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

BOOKS_PROCESSING_PROGRESS_KEY = "books:processing_progress"


def _status_value(status: str) -> str:
    return status.value if hasattr(status, "value") else str(status)


def set_book_processing_cache(
    book_id: UUID,
    status: str,
    progress: float,
    error: str | None = None,
) -> None:
    payload = {
        "book_id": str(book_id),
        "status": _status_value(status),
        "progress": round(progress, 2),
    }

    if error:
        payload["error"] = error

    redis_client.hset(
        BOOKS_PROCESSING_PROGRESS_KEY,
        str(book_id),
        json.dumps(payload),
    )
