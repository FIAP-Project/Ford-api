from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from audit_service.config import get_settings
from audit_service.controllers import audit_router, health_router
from audit_service.events import start_consumers
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
    await app.state.event_bus.connect()
    await start_consumers(
        app.state.event_bus, app.state.database, settings.event_signing_secret
    )
    logger.info("audit-service startup complete")
    try:
        yield
    finally:
        await app.state.event_bus.close()
        await app.state.database.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Ford Audit Service",
        version="0.1.0",
        description="Wildcard consumer that persists every event for compliance.",
        docs_url="/audit/docs",
        openapi_url="/audit/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    apply_standard_middleware(app, settings.cors_allowed_origins)
    app.include_router(health_router, prefix="/audit")
    app.include_router(audit_router)
    return app


app = create_app()
