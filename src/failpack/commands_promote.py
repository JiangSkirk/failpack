"""failpack promote — mark a pack golden and write assertions.yaml."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from failpack.assertions_schema import validate_assertions
from failpack.diffutil import write_expected_snapshot
from failpack.events import bash_outputs, denied_tool_names, load_pack_events
from failpack.pack import (
    artifacts_dir,
    glob_fingerprint,
    read_meta,
    sha256_file,
    utc_now_iso,
    write_assertions,
    write_meta,
)
from failpack.paths import TRANSCRIPT_NAME, require_pack
from failpack.schema import with_current_schema


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


def _pick_bash_needles(outputs: list[str]) -> list[dict[str, str]]:
    """Pick distinctive bash_output_contains needles from tool results."""
    if not outputs:
        return []
    suggestions: list[dict[str, str]] = []
    seen: set[str] = set()

    def _add(needle: str, *, match: str) -> None:
        needle = needle.strip()
        if len(needle) < 8:
            return
        needle = needle[:120]
        key = f"{match}:{needle}"
        if key in seen:
            return
        seen.add(key)
        suggestions.append({"contains": needle, "match": match})

    # Prefer last Bash output for the session's final failure signal
    last = outputs[-1]
    for line in last.splitlines():
        line = line.strip()
        if len(line) >= 12 and re.search(
            r"(error|denied|fail|traceback|exception|not found|exit)", line, re.I
        ):
            _add(line, match="last")
            break
    if not any(s.get("match") == "last" for s in suggestions) and last.strip():
        # Fall back to a stable chunk of the last output
        chunk = next(
            (ln.strip() for ln in last.splitlines() if len(ln.strip()) >= 12),
            last.strip()[:80],
        )
        _add(chunk, match="last")

    # Also suggest a distinctive "any" needle from earlier outputs when useful
    for out in outputs:
        for line in out.splitlines():
            line = line.strip()
            if len(line) < 8:
                continue
            if re.search(r"\.(toml|json|ya?ml|py|lock)\b", line) or re.search(
                r"\b(pyproject|package\.json|Cargo\.toml)\b", line
            ):
                _add(line.split()[0] if " " in line and len(line.split()[0]) >= 8 else line, match="any")
                break
        if any(s.get("match") == "any" for s in suggestions):
            break

    return suggestions


def suggest_assertions(pack: Path, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Analyze pack artifacts + transcript and recommend golden assertions.

    Extends the default fingerprint/exit_code set with transcript-derived
    ``tool_denied_contains`` / ``bash_output_contains`` when signals exist.
    """
    if meta is None:
        meta = read_meta(pack)
    assertions = _default_assertions(pack, meta)

    transcript = pack / TRANSCRIPT_NAME
    if transcript.is_file():
        try:
            events = load_pack_events(transcript)
        except (OSError, ValueError):
            events = []
        if events:
            denied = denied_tool_names(events)
            if denied:
                assertions["tool_denied_contains"] = [
                    {"contains": name} for name in denied
                ]
            outs = bash_outputs(events)
            bash_needles = _pick_bash_needles(outs)
            if bash_needles:
                assertions["bash_output_contains"] = bash_needles

    return validate_assertions(assertions)


def format_suggest_preview(assertions: dict[str, Any], *, pack_id: str) -> str:
    """Human-readable recommendation header + YAML body for ``--suggest``."""
    lines: list[str] = [
        f"# Suggested assertions for '{pack_id}'",
        "# Analyzed: artifacts + transcript events (ticks)",
        "#",
        "# Recommendations:",
    ]
    if "exit_code" in assertions:
        lines.append(f"#   exit_code: {assertions['exit_code']}")
    fps = assertions.get("fingerprints") or []
    if fps:
        paths = ", ".join(fp["path"] for fp in fps[:8])
        more = f" (+{len(fps) - 8} more)" if len(fps) > 8 else ""
        lines.append(f"#   fingerprints: {len(fps)} path(s) — {paths}{more}")
    for entry in assertions.get("tool_denied_contains") or []:
        needle = entry if isinstance(entry, str) else entry.get("contains")
        lines.append(f"#   tool_denied_contains: {needle}")
    for entry in assertions.get("bash_output_contains") or []:
        if isinstance(entry, str):
            lines.append(f"#   bash_output_contains: {entry!r}")
        else:
            match = entry.get("match") or "any"
            lines.append(
                f"#   bash_output_contains: {entry.get('contains')!r} (match={match})"
            )
    if not assertions.get("tool_denied_contains") and not assertions.get(
        "bash_output_contains"
    ):
        lines.append(
            "#   (no tool_denied / bash_output signals found — "
            "fingerprints + exit_code only)"
        )
    lines.append("#")
    lines.append(f"# Apply with: failpack promote --suggest --write {pack_id}")
    lines.append("# Or keep editing the YAML below before writing.")
    lines.append("")
    lines.append(format_assertions_preview(assertions))
    return "\n".join(lines)


def _write_expected_snapshots(pack: Path, fingerprints: list[dict[str, str]]) -> None:
    """Snapshot fingerprinted text artifacts for diff-aware explain on FAIL."""
    expected_root = pack / "expected"
    if expected_root.exists():
        shutil.rmtree(expected_root)
    for fp in fingerprints:
        rel = fp["path"]
        write_expected_snapshot(pack, rel, pack / rel)


def format_assertions_preview(assertions: dict[str, Any]) -> str:
    """YAML text for dry-run / preview output."""
    return yaml.safe_dump(assertions, sort_keys=False, default_flow_style=False)


def cmd_promote(
    pack_id: str,
    *,
    root: Path | None = None,
    dry_run: bool = False,
    suggest: bool = False,
    write: bool = False,
) -> Path | dict[str, Any]:
    """Promote a pack to golden.

    * ``suggest=True`` (no write): return suggested assertions for preview.
    * ``suggest=True`` + ``write=True``: write suggested assertions (smarter).
    * default / ``write`` without suggest: write suggested assertions
      (smarter promote — same builder as ``--suggest``).
    * ``dry_run=True``: return assertions that would be written (no filesystem
      changes). Cannot combine with ``suggest`` (use one preview mode).

    When *dry_run* or *suggest* (without *write*), return the assertions dict
    without touching the filesystem.
    """
    if dry_run and suggest:
        raise ValueError("Use --suggest or --dry-run, not both.")
    if write and dry_run:
        raise ValueError("Use --write or --dry-run, not both.")
    if write and not suggest:
        # Allow --write alone as explicit "apply" alias for promote write path
        pass

    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    # Smarter promote: always build from transcript+artifacts suggestions
    assertions = suggest_assertions(pack, meta)

    preview_only = dry_run or (suggest and not write)
    if preview_only:
        return assertions

    write_assertions(pack, assertions)
    _write_expected_snapshots(pack, assertions.get("fingerprints") or [])
    meta["status"] = "golden"
    meta["promoted_at"] = utc_now_iso()
    write_meta(pack, with_current_schema(meta))
    return pack


def cmd_re_promote(
    pack_id: str,
    *,
    root: Path | None = None,
    dry_run: bool = False,
    suggest: bool = False,
    write: bool = False,
) -> Path | dict[str, Any]:
    """Refresh golden assertions from *current* pack artifacts.

    Common workflow after intentional drift: fix the failure, update artifacts
    (or accept the new golden signals), then ``failpack re-promote <id>`` so
    ``assertions.yaml`` + expected snapshots match again.
    """
    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    if meta.get("status") not in {"golden", "captured"}:
        # Still allow refresh when status is odd but pack exists
        pass
    return cmd_promote(
        pack_id,
        root=root,
        dry_run=dry_run,
        suggest=suggest,
        write=write,
    )
