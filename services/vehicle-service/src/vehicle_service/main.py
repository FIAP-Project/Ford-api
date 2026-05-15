from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from ford_shared.app import apply_standard_middleware
from ford_shared.db import Database
from ford_shared.events import EventBus
from ford_shared.security.jwt import JWTService
from vehicle_service.config import get_settings
from vehicle_service.controllers import health_router, vehicle_router
from vehicle_service.controllers.vehicle_controller import limiter
from vehicle_service.services import ClaudeClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app.state.settings = settings
    app.state.database = Database(settings.database_url)
    app.state.event_bus = EventBus(
        amqp_url=settings.amqp_url,
        signing_secret=settings.event_signing_secret,
    )
    app.state.jwt_service = JWTService(
        secret_key=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        access_token_ttl_minutes=settings.access_token_ttl_minutes,
        refresh_token_ttl_days=settings.refresh_token_ttl_days,
    )
    app.state.claude_client = ClaudeClient(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
        timeout_seconds=settings.claude_timeout_seconds,
    )
    await app.state.event_bus.connect()
    logger.info("vehicle-service startup complete")
    try:
        yield
    finally:
        await app.state.event_bus.close()
        await app.state.database.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Ford Vehicle Service",
        version="0.1.0",
        description=(
            "Receives brand/model/version + attributes, asks Claude for specs, "
            "and returns a standardized normalized list."
        ),
        docs_url="/vehicles/docs",
        openapi_url="/vehicles/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    apply_standard_middleware(app, settings.cors_allowed_origins)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(health_router, prefix="/vehicles")
    app.include_router(vehicle_router)
    return app


app = create_app()
