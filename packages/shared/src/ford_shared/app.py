"""Helpers to wire up a FastAPI app with the standard middleware stack."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ford_shared.middleware import (
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    register_exception_handlers,
)


def apply_standard_middleware(app: FastAPI, cors_allowed_origins: list[str]) -> None:
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Signature"],
        max_age=600,
    )
    register_exception_handlers(app)
