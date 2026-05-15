"""Pydantic schemas for the /vehicles endpoints.

Validation focus:
- Strings are stripped + length-limited (no payload flooding).
- Regex rejects shell metachars / control chars (defense against injection in prompts).
- The attributes list is bounded by `max_attributes_per_query`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SAFE_TEXT = r"^[\w\s\-\.\,\/\(\)\+]+$"


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    brand: str = Field(..., min_length=1, max_length=80, pattern=_SAFE_TEXT)
    model: str = Field(..., min_length=1, max_length=120, pattern=_SAFE_TEXT)
    version: str = Field(..., min_length=1, max_length=120, pattern=_SAFE_TEXT)
    attributes: list[str] = Field(..., min_length=1, max_length=30)

    @field_validator("attributes")
    @classmethod
    def _validate_attributes(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in value:
            attr = raw.strip().lower()
            if not attr or len(attr) > 80:
                raise ValueError("attribute names must be 1-80 chars")
            if not all(c.isalnum() or c in {"_", "-", " ", "/"} for c in attr):
                raise ValueError("attribute names can only contain alphanumerics, _ - / space")
            if attr in seen:
                continue
            seen.add(attr)
            cleaned.append(attr)
        return cleaned


class SpecOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attribute: str
    value: str | None
    available: bool
    normalized_unit: str | None = None
    source_hint: str | None = None


class QueryResponse(BaseModel):
    id: UUID
    user_id: UUID
    brand: str
    model: str
    version: str
    status: str
    created_at: datetime
    specs: list[SpecOut]


class QuerySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand: str
    model: str
    version: str
    status: str
    created_at: datetime
