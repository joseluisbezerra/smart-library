from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "worker",
    broker=settings.redis_url,
    backend=None,
)
