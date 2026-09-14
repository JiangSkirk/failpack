"""Filesystem helpers for the .failpack layout."""

from __future__ import annotations

from pathlib import Path

FAILPACK_DIR = ".failpack"
PACKS_DIR = "packs"
ARTIFACTS_DIR = "artifacts"
TRANSCRIPT_NAME = "transcript.jsonl"
META_NAME = "meta.json"
ASSERTIONS_NAME = "assertions.yaml"


def find_root(start: Path | None = None) -> Path:
    """Walk up from start (or cwd) looking for .failpack/; else use cwd.

    Used by list/replay/status/show/promote/etc. so nested workdirs still find
    an already-discovered pack workspace. Setup/write entry points (demo, init,
    capture) and doctor use ``local_root`` instead — they must not silently
    write into or score an ancestor ``.failpack/``.
    """
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / FAILPACK_DIR).is_dir():
            return candidate
    return cur


def local_root(root: Path | None = None) -> Path:
    """cwd or explicit ``--root`` only — never climbs to ancestor ``.failpack/``.

    Used by:
    - ``failpack doctor`` (score the directory the stranger is in)
    - ``failpack demo`` / ``init`` / first-time ``capture`` (create or write
      packs under cwd, not a parent layout)

    Pass ``--root`` to target another project. Commands that operate on an
    already-discovered pack tree still climb via ``find_root``.
    """
    return (root or Path.cwd()).resolve()


def doctor_root(root: Path | None = None) -> Path:
    """Project root for ``failpack doctor`` — alias of ``local_root``."""
    return local_root(root)


def failpack_dir(root: Path | None = None) -> Path:
    return (root or find_root()) / FAILPACK_DIR


def packs_dir(root: Path | None = None) -> Path:
    return failpack_dir(root) / PACKS_DIR


def pack_dir(pack_id: str, root: Path | None = None) -> Path:
    return packs_dir(root) / pack_id


def require_pack(pack_id: str, root: Path | None = None) -> Path:
    path = pack_dir(pack_id, root)
    if not path.is_dir():
        raise FileNotFoundError(
            f"Pack '{pack_id}' not found under {packs_dir(root)}. "
            f"Run `failpack capture` or check the id."
        )
    return path
