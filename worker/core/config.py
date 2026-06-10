from functools import lru_cache
from os import getenv


class Settings:
    postgres_user: str = getenv("POSTGRES_USER", "postgres")
    postgres_password: str = getenv("POSTGRES_PASSWORD", "postgres")
    postgres_db: str = getenv("POSTGRES_DB", "smart_library")
    postgres_host: str = getenv("POSTGRES_HOST", "pgvector")
    postgres_port: str = getenv("POSTGRES_PORT", "5432")
    redis_password: str = getenv("REDIS_PASSWORD", "")
    redis_host: str = getenv("REDIS_HOST", "redis")
    redis_port: str = getenv("REDIS_PORT", "6379")
    redis_db: str = getenv("REDIS_DB", "0")

    openai_embedding_model: str = getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small"
    )

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""

        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
