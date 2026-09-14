"""failpack rm — delete a pack directory."""

from __future__ import annotations

import shutil
from pathlib import Path

from failpack.pack import read_meta
from failpack.paths import require_pack


def cmd_rm(
    pack_id: str,
    *,
    root: Path | None = None,
    force: bool = False,
) -> Path:
    """Delete ``.failpack/packs/<id>/``.

    Refuses without ``--force`` when the pack status is ``golden``.
    """
    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    status = str(meta.get("status") or "")
    if status == "golden" and not force:
        raise ValueError(
            f"Pack '{pack_id}' is golden; pass --force to delete "
            f"(or demote/rename first)."
        )
    shutil.rmtree(pack)
    return pack
