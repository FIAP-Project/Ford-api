"""Normalize Claude's spec list into the contract our API guarantees.

Contract:
- The response MUST contain exactly one entry per attribute the user requested.
- Missing attributes are filled with `{value: None, available: False}`.
- Attribute order in the response mirrors the order requested by the user.
- Strings are stripped; empty strings become `None` with `available=False`.
"""

from __future__ import annotations

from vehicle_service.services.claude_client import ClaudeSpec


def normalize_specs(
    requested: list[str], from_claude: list[ClaudeSpec]
) -> list[ClaudeSpec]:
    by_attr = {spec.attribute.strip().lower(): spec for spec in from_claude}

    normalized: list[ClaudeSpec] = []
    for raw_attr in requested:
        key = raw_attr.strip().lower()
        spec = by_attr.get(key)
        if spec is None:
            normalized.append(
                ClaudeSpec(attribute=raw_attr, value=None, available=False)
            )
            continue

        # Sanitize: empty string → None + unavailable
        value = (spec.value or "").strip() or None
        if value is None and spec.available:
            normalized.append(
                ClaudeSpec(
                    attribute=raw_attr,
                    value=None,
                    available=False,
                    normalized_unit=spec.normalized_unit,
                    source_hint=spec.source_hint,
                )
            )
            continue

        normalized.append(
            ClaudeSpec(
                attribute=raw_attr,
                value=value,
                available=spec.available and value is not None,
                normalized_unit=spec.normalized_unit,
                source_hint=spec.source_hint,
            )
        )
    return normalized
