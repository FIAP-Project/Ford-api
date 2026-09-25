"""Prometheus metrics shared by every service.

`instrument_app` wires a single middleware that records request count and
latency per (service, method, path template, status) and exposes them on
`GET /metrics` for Prometheus to scrape. Route-specific counters (e.g. the
Claude API calls in vehicle-service) are defined next to their call site and
reuse the same default registry.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled",
    ["service", "method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "path"],
)


def instrument_app(app: FastAPI, service_name: str) -> None:
    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        started = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - started

        path = request.scope.get("route").path if request.scope.get("route") else request.url.path
        HTTP_REQUESTS_TOTAL.labels(
            service=service_name,
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            service=service_name, method=request.method, path=path
        ).observe(duration)

        return response

    @app.get("/metrics", include_in_schema=False)
    async def _metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
