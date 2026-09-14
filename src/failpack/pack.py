"""Shared pack metadata and assertion models (plain dicts + YAML)."""

from __future__ import annotations

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
