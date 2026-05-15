"""Wildcard event consumer — persists EVERY event for compliance review.

We bind a single queue to `#` (RabbitMQ topic wildcard for "everything")
so the audit trail is canonical regardless of producer.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from audit_service.repositories import EventRepository
from ford_shared.db import Database
from ford_shared.events import EventBus, EventEnvelope
from ford_shared.security.signature import sign_payload

logger = logging.getLogger(__name__)


def make_audit_handler(database: Database, signing_secret: str):
    async def _handle(envelope: EventEnvelope) -> None:
        payload = envelope.payload
        actor = payload.get("actor_user_id")
        actor_id: UUID | None = UUID(actor) if actor else None
        event_type = payload.get("event_type") or envelope.routing_key
        occurred_raw = payload.get("occurred_at")

        occurred_at: datetime
        if isinstance(occurred_raw, str):
            try:
                occurred_at = datetime.fromisoformat(occurred_raw)
            except ValueError:
                occurred_at = datetime.now()
        else:
            occurred_at = datetime.now()

        signature = sign_payload(envelope.raw_body, signing_secret)

        async for session in database.session():
            repo = EventRepository(session)
            await repo.append(
                event_type=event_type,
                routing_key=envelope.routing_key,
                actor_user_id=actor_id,
                payload=payload,
                occurred_at=occurred_at,
                signature=signature,
            )
        logger.info(
            "audit.event_persisted",
            extra={"event_type": event_type, "routing_key": envelope.routing_key},
        )

    return _handle


async def start_consumers(
    event_bus: EventBus, database: Database, signing_secret: str
) -> None:
    await event_bus.subscribe(
        queue_name="audit-service.all",
        routing_keys=["#"],
        handler=make_audit_handler(database, signing_secret),
    )
