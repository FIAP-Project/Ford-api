"""Safe global exception handlers.

Goal: never leak stack traces, ORM strings, or framework internals to clients.
Full detail is logged server-side with a request_id correlation marker.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def _safe_response(status_code: int, message: str, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": status_code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http_exc(request: Request, exc: HTTPException) -> JSONResponse:
        rid = _request_id(request)
        logger.info(
            "http_exception",
            extra={"status": exc.status_code, "detail": exc.detail, "request_id": rid},
        )
        return _safe_response(exc.status_code, str(exc.detail), rid)

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        rid = _request_id(request)
        # Pydantic errors are safe to surface in summary form — they describe
        # field-level validation issues, not internals. Sanitize "ctx" objects
        # that may contain Python repr of values.
        safe_errors = [
            {
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ]
        logger.info(
            "validation_error",
            extra={"errors": safe_errors, "request_id": rid},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": 422,
                    "message": "Validation failed",
                    "details": safe_errors,
                    "request_id": rid,
                }
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        rid = _request_id(request)
        logger.exception("unhandled_exception", extra={"request_id": rid})
        return _safe_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error",
            rid,
        )
