"""Base configuration shared by all services.

Each service extends BaseServiceSettings with service-specific fields.
Values are read from environment variables; pydantic-settings validates
types and required fields. .env file loading is supported for local dev.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    service_name: str
    environment: str = "dev"
    log_level: str = "INFO"

    database_url: str = Field(
        ...,
        description="postgresql+asyncpg://user:pass@host:5432/db",
    )
    db_schema: str = Field(..., description="Schema this service owns")

    amqp_url: str = Field(..., description="amqp://user:pass@host:5672/")
    event_signing_secret: str = Field(..., min_length=32)

    jwt_secret: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["https://localhost"])
