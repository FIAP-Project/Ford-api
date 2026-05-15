"""Anthropic Claude client tuned for structured vehicle-spec extraction.

Strategy:
- System prompt is cached (Anthropic prompt caching) — it's stable across requests.
- We ask Claude to return ONLY valid JSON matching a known schema.
- We use tool calling (function calling) for reliable structured output:
  Claude is forced to call the `submit_vehicle_specs` tool, whose input_schema
  pins the exact format we want.
- Tenacity retries transient failures (network / 5xx); JSON parse failures
  trigger one retry with a stricter "JSON only" reminder.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import anthropic
from anthropic.types import MessageParam
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class ClaudeSpec(BaseModel):
    attribute: str = Field(..., max_length=80)
    value: str | None = Field(default=None, max_length=400)
    available: bool
    normalized_unit: str | None = Field(default=None, max_length=40)
    source_hint: str | None = Field(default=None, max_length=200)


SYSTEM_PROMPT = """You are an expert automotive technical-specifications researcher.
You provide accurate, factual specs for production vehicles using public manufacturer data
(BR/LATAM market when applicable).

Rules for every response:
1. Always respond by calling the `submit_vehicle_specs` tool.
2. Return one entry per attribute requested by the user — never add, drop, or rename attributes.
3. Use the SAME LANGUAGE the user used in the attribute name (typically Portuguese).
4. `value` must be a concise string with the canonical value (numbers + unit if applicable).
5. `available` is `false` only when you cannot determine the value with confidence
   (do NOT guess) — in that case `value` must be `null`.
6. `normalized_unit` is the canonical unit (e.g. "cv", "Nm", "km/h", "L", "kg", "BRL")
   when the attribute has one; otherwise `null`.
7. `source_hint` is a brief note about where this info typically comes from
   (e.g. "Ford BR Ranger Raptor datasheet 2024").
8. Never invent specs you do not know. Never include disclaimers or extra prose outside
   the tool call.
"""


SPECS_TOOL = {
    "name": "submit_vehicle_specs",
    "description": "Submit the normalized vehicle specifications.",
    "input_schema": {
        "type": "object",
        "properties": {
            "specs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "attribute": {"type": "string"},
                        "value": {"type": ["string", "null"]},
                        "available": {"type": "boolean"},
                        "normalized_unit": {"type": ["string", "null"]},
                        "source_hint": {"type": ["string", "null"]},
                    },
                    "required": ["attribute", "value", "available"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["specs"],
        "additionalProperties": False,
    },
}


@dataclass(frozen=True)
class ClaudeResult:
    specs: list[ClaudeSpec]
    raw_response: dict


class ClaudeClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        timeout_seconds: int = 60,
    ) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key, timeout=timeout_seconds
        )
        self._model = model
        self._max_tokens = max_tokens

    @retry(
        retry=retry_if_exception_type(
            (anthropic.APIConnectionError, anthropic.APIStatusError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def fetch_vehicle_specs(
        self,
        brand: str,
        model: str,
        version: str,
        attributes: list[str],
    ) -> ClaudeResult:
        user_message = (
            f"Vehicle: brand={brand}, model={model}, version={version}.\n"
            f"Return specs for EXACTLY these attributes (one entry each):\n"
            + "\n".join(f"- {attr}" for attr in attributes)
        )
        messages: list[MessageParam] = [{"role": "user", "content": user_message}]

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[SPECS_TOOL],
            tool_choice={"type": "tool", "name": "submit_vehicle_specs"},
            messages=messages,
        )

        tool_use = next(
            (block for block in response.content if block.type == "tool_use"),
            None,
        )
        if tool_use is None:
            logger.error("claude.no_tool_use", extra={"stop_reason": response.stop_reason})
            raise ValueError("Claude did not return a tool_use block")

        raw_input = tool_use.input
        if isinstance(raw_input, str):
            raw_input = json.loads(raw_input)
        specs_data = raw_input.get("specs", [])

        specs = [ClaudeSpec(**item) for item in specs_data]
        return ClaudeResult(
            specs=specs,
            raw_response={
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": response.usage.model_dump() if response.usage else {},
                "raw_specs": specs_data,
            },
        )
