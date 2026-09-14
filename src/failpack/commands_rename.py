"""failpack rename — rename a pack id and update meta."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from failpack.ids import validate_pack_id
from failpack.pack import read_assertions, read_meta, write_assertions, write_meta
from failpack.paths import ASSERTIONS_NAME, pack_dir, require_pack
from failpack.schema import with_current_schema


def cmd_rename(
    old_id: str,
    new_id: str,
    *,
    root: Path | None = None,
) -> Path:
    """Rename pack directory and update ``meta.id`` (and assertions ``pack_id``)."""
    old_id = validate_pack_id(old_id)
    new_id = validate_pack_id(new_id)
    if old_id == new_id:
        raise ValueError(f"Old and new pack ids are the same: {old_id!r}")

    old_pack = require_pack(old_id, root)
    new_pack = pack_dir(new_id, root)
    if new_pack.exists():
        raise FileExistsError(
            f"Pack '{new_id}' already exists under {new_pack.parent}. "
            f"Choose a different id or remove the existing pack first."
        )

    meta = read_meta(old_pack)
    assertions: dict[str, Any] | None = None
    if (old_pack / ASSERTIONS_NAME).is_file():
        assertions = read_assertions(old_pack)

    old_pack.rename(new_pack)

    meta["id"] = new_id
    write_meta(new_pack, with_current_schema(meta))

    if assertions is not None:
        assertions["pack_id"] = new_id
        write_assertions(new_pack, assertions)

    return new_pack
