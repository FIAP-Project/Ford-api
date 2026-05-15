from __future__ import annotations

from functools import lru_cache

from ford_shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "audit-service"
    db_schema: str = "audit"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
