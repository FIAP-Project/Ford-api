from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from ford_shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "vehicle-service"
    db_schema: str = "vehicle"

    anthropic_api_key: str = Field(..., description="Claude API key")
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 4096
    claude_timeout_seconds: int = 60

    redis_url: str = "redis://redis:6379/1"
    query_rate_limit: str = "20/minute"

    max_attributes_per_query: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
