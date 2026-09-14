"""failpack promote — mark a pack golden and write assertions.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from failpack.pack import (
    artifacts_dir,
    glob_fingerprint,
    read_meta,
    sha256_file,
    utc_now_iso,
    write_assertions,
    write_meta,
)
from failpack.paths import require_pack


def _default_assertions(pack: Path, meta: dict[str, Any]) -> dict[str, Any]:
    arts = artifacts_dir(pack)
    fingerprints: list[dict[str, str]] = []
    for rel in ("digest.json", "exit_code.txt", "status.txt", "error.txt", "summary.md"):
        path = arts / rel
        if path.is_file():
            fingerprints.append(
                {
                    "path": f"artifacts/{rel}",
                    "sha256": sha256_file(path),
                }
            )

    # fingerprint any written files under artifacts/files/
    files_root = arts / "files"
    if files_root.is_dir():
        for path in sorted(files_root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(pack).as_posix()
                fingerprints.append({"path": rel, "sha256": sha256_file(path)})

    exit_code = int((arts / "exit_code.txt").read_text(encoding="utf-8").strip())
    error_text = (arts / "error.txt").read_text(encoding="utf-8")

    substrings: list[dict[str, str]] = []
    # Prefer a distinctive non-empty error line as expected failure signal
    for line in error_text.splitlines():
        line = line.strip()
        if len(line) >= 12:
            substrings.append({"path": "artifacts/error.txt", "contains": line[:120]})
            break
    if not substrings and error_text.strip():
        substrings.append(
            {"path": "artifacts/error.txt", "contains": error_text.strip()[:80]}
        )

    assertions: dict[str, Any] = {
        "version": 1,
        "pack_id": meta["id"],
        "description": (
            "Golden assertions for this failure session. "
            "Replay fails CI if fingerprints or expected signals drift."
        ),
        "exit_code": exit_code,
        "fingerprints": fingerprints,
        "substrings": substrings,
    }

    # Optional stronger checks (backward compatible — older packs omit these)
    event_count = meta.get("event_count")
    if event_count is not None:
        assertions["min_events"] = int(event_count)

    if files_root.is_dir() and any(files_root.rglob("*")):
        pattern = "artifacts/files/**"
        digest, matched = glob_fingerprint(pack, pattern)
        if matched:
            assertions["glob_fingerprint"] = {
                "pattern": pattern,
                "sha256": digest,
                "file_count": len(matched),
            }

    return assertions


def cmd_promote(pack_id: str, *, root: Path | None = None) -> Path:
    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    assertions = _default_assertions(pack, meta)
    write_assertions(pack, assertions)
    meta["status"] = "golden"
    meta["promoted_at"] = utc_now_iso()
    write_meta(pack, meta)
    return pack
