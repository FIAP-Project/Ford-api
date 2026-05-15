"""Event handlers — keeps user_profiles in sync with auth events."""

from __future__ import annotations

import logging
from uuid import UUID

from ford_shared.db import Database
from ford_shared.events import EventBus, EventEnvelope, EventType
from user_service.repositories import ProfileRepository

logger = logging.getLogger(__name__)


def make_user_registered_handler(database: Database):
    async def _handle(envelope: EventEnvelope) -> None:
        payload = envelope.payload
        auth_user_id = UUID(payload["user_id"])
        email = payload["email"]
        role = payload.get("role", "user")
        full_name = payload.get("full_name")

        async for session in database.session():
            repo = ProfileRepository(session)
            await repo.upsert_from_event(
                auth_user_id=auth_user_id,
                email=email,
                role=role,
                full_name=full_name,
            )
            logger.info(
                "profile.upserted_from_event",
                extra={"auth_user_id": str(auth_user_id), "email": email},
            )

    return _handle


async def start_consumers(event_bus: EventBus, database: Database) -> None:
    await event_bus.subscribe(
        queue_name="user-service.user-registered",
        routing_keys=[EventType.USER_REGISTERED.value],
        handler=make_user_registered_handler(database),
    )
