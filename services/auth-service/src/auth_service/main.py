"""auth-service FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from auth_service.config import get_settings
from auth_service.controllers import auth_router, health_router
from auth_service.controllers.auth_controller import limiter
from ford_shared.app import apply_standard_middleware
from ford_shared.db import Database
from ford_shared.events import EventBus
from ford_shared.security.jwt import JWTService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app.state.settings = settings
    app.state.database = Database(settings.database_url, echo=False)
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
    await app.state.event_bus.connect()
    logger.info("auth-service startup complete")
    try:
        yield
    finally:
        await app.state.event_bus.close()
        await app.state.database.dispose()
        logger.info("auth-service shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Ford Auth Service",
        version="0.1.0",
        description="Register, login, refresh — JWT-based authentication.",
        docs_url="/auth/docs",
        openapi_url="/auth/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    apply_standard_middleware(app, settings.cors_allowed_origins)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(health_router, prefix="/auth")
    app.include_router(auth_router)
    return app


app = create_app()
