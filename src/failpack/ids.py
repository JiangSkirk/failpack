"""Pack id validation helpers."""

from __future__ import annotations

import re

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_pack_id(pack_id: str) -> str:
    if not _SAFE_ID.match(pack_id):
        raise ValueError(
            f"Invalid pack id {pack_id!r}. Use letters, digits, '.', '_', '-' "
            "(max 128 chars)."
        )
    return pack_id
