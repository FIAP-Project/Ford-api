"""Event payload schemas published to RabbitMQ.

Routing key conventions:
- user.registered
- user.logged_in
- auth.failed
- vehicle.query.requested
- vehicle.query.completed
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"
    AUTH_FAILED = "auth.failed"
    VEHICLE_QUERY_REQUESTED = "vehicle.query.requested"
    VEHICLE_QUERY_COMPLETED = "vehicle.query.completed"


class _BaseEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: EventType
    occurred_at: datetime
    actor_user_id: str | None = None


class UserRegisteredEvent(_BaseEvent):
    event_type: EventType = EventType.USER_REGISTERED
    user_id: str
    email: str
    role: str


class UserLoggedInEvent(_BaseEvent):
    event_type: EventType = EventType.USER_LOGGED_IN
    user_id: str
    email: str


class AuthFailedEvent(_BaseEvent):
    event_type: EventType = EventType.AUTH_FAILED
    email: str
    reason: str


class VehicleQueryRequestedEvent(_BaseEvent):
    event_type: EventType = EventType.VEHICLE_QUERY_REQUESTED
    query_id: str
    user_id: str
    brand: str
    model: str
    version: str
    attributes: list[str]


class VehicleQueryCompletedEvent(_BaseEvent):
    event_type: EventType = EventType.VEHICLE_QUERY_COMPLETED
    query_id: str
    user_id: str
    status: str
    spec_count: int = 0
    duration_ms: int = 0


class GenericEvent(_BaseEvent):
    """Fallback model used by audit-service to capture any event payload."""

    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
