"""Pack schema version constants and helpers."""

from __future__ import annotations

from typing import Any

# Bump when pack layout / meta / assertion semantics need a migration step.
CURRENT_SCHEMA_VERSION = 1

SCHEMA_VERSION_KEY = "schema_version"


def schema_version_of(meta: dict[str, Any]) -> int:
    """Return pack schema version; packs without the field are treated as 0."""
    raw = meta.get(SCHEMA_VERSION_KEY)
    if raw is None:
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def with_current_schema(meta: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *meta* stamped with the current schema version."""
    out = dict(meta)
    out[SCHEMA_VERSION_KEY] = CURRENT_SCHEMA_VERSION
    return out
