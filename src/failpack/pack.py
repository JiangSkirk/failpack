"""Shared pack metadata and assertion models (plain dicts + YAML)."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from failpack.paths import (
    ASSERTIONS_NAME,
    ARTIFACTS_DIR,
    META_NAME,
    TRANSCRIPT_NAME,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def glob_fingerprint(pack: Path, pattern: str) -> tuple[str, list[str]]:
    """SHA-256 over sorted ``relpath=file_sha256`` lines for files matching *pattern*.

    *pattern* is relative to the pack root (e.g. ``artifacts/files/**``).
    Returns ``(digest, matched_relative_paths)``.
    """
    matched: list[Path] = []
    for path in pack.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(pack).as_posix()
        if fnmatch.fnmatch(rel, pattern):
            matched.append(path)

    matched.sort(key=lambda p: p.relative_to(pack).as_posix())
    lines: list[str] = []
    rels: list[str] = []
    for path in matched:
        rel = path.relative_to(pack).as_posix()
        rels.append(rel)
        lines.append(f"{rel}={sha256_file(path)}")
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    return sha256_bytes(payload), rels


def read_meta(pack: Path) -> dict[str, Any]:
    return json.loads((pack / META_NAME).read_text(encoding="utf-8"))


def write_meta(pack: Path, meta: dict[str, Any]) -> None:
    (pack / META_NAME).write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_assertions(pack: Path) -> dict[str, Any]:
    path = pack / ASSERTIONS_NAME
    if not path.exists():
        raise FileNotFoundError(
            f"No {ASSERTIONS_NAME} in {pack.name}. Run `failpack promote {pack.name}` first."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid assertions file: {path}")
    return data


def write_assertions(pack: Path, assertions: dict[str, Any]) -> None:
    (pack / ASSERTIONS_NAME).write_text(
        yaml.safe_dump(assertions, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def artifacts_dir(pack: Path) -> Path:
    return pack / ARTIFACTS_DIR


def transcript_path(pack: Path) -> Path:
    return pack / TRANSCRIPT_NAME
