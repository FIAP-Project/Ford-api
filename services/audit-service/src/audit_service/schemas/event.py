from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    routing_key: str
    actor_user_id: UUID | None
    payload: dict[str, Any]
    occurred_at: datetime
    signature: str
