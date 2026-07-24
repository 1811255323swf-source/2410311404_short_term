"""Deterministic validation for AI coaching output.

This module is deliberately independent from HTTP clients and model SDKs so
contract tests can run offline with the Python standard library.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REQUIRED_FIELDS = (
    "summary",
    "repair_order",
    "concept_links",
    "exercises",
)
LIST_FIELDS = (
    "repair_order",
    "concept_links",
    "exercises",
)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def validate_ai_coaching(payload: object) -> tuple[bool, list[str]]:
    """Return a stable validity flag and machine-readable error list."""

    if not isinstance(payload, Mapping):
        return False, ["type:root"]

    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing:{field}")

    summary = payload.get("summary")
    if "summary" in payload and not (
        isinstance(summary, str) and bool(summary.strip())
    ):
        errors.append("type:summary")

    for field in LIST_FIELDS:
        if field in payload and not _is_string_list(payload[field]):
            errors.append(f"type:{field}")

    return not errors, errors
