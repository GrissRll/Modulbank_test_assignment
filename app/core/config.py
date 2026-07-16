from functools import lru_cache

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    provider_url: AnyHttpUrl

    provider_request_timeout: float = 5.0
    provider_max_retries: int = 5

    worker_poll_interval: float = 1.0
    worker_batch_size: int = 10

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
