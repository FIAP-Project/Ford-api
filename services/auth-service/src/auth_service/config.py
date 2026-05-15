"""auth-service settings."""

from __future__ import annotations

from functools import lru_cache

from ford_shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "auth-service"
    db_schema: str = "auth"

    redis_url: str = "redis://redis:6379/0"
    login_rate_limit: str = "5/minute"
    register_rate_limit: str = "10/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
