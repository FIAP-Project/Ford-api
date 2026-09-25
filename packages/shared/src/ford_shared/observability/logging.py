"""JSON structured logging, shared by every service.

Wraps stdlib logging with structlog's ProcessorFormatter so every existing
`logging.getLogger(__name__).info(...)` call in the codebase (controllers,
event bus, consumers, error handlers) is rendered as a single JSON line —
no call sites need to change. `extra={...}` kwargs passed to stdlib logging
(e.g. request_id, event_type) are merged into the JSON output automatically.
"""

from __future__ import annotations

import logging
import sys

import structlog

_SHARED_PROCESSORS = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.ExtraAdder(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]


def configure_logging(service_name: str, level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=_SHARED_PROCESSORS,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for noisy in ("uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(noisy)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)
