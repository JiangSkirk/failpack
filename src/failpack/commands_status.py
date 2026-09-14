"""failpack status — show meta + assertion summary for one pack."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from failpack.pack import read_assertions, read_meta
from failpack.paths import ASSERTIONS_NAME, require_pack


@dataclass
class StatusReport:
    pack_id: str
    meta: dict[str, Any]
    assertions: dict[str, Any] | None = None
    assertion_summary: list[str] = field(default_factory=list)

    def summary_lines(self) -> list[str]:
        m = self.meta
        lines = [
            f"failpack status: {self.pack_id}",
            f"  status:       {m.get('status', 'unknown')}",
            f"  schema:       {m.get('schema_version', '(unset)')}",
            f"  exit_code:    {m.get('exit_code', '-')}",
            f"  events:       {m.get('event_count', '-')}",
            f"  session_id:   {m.get('session_id') or '-'}",
            f"  created_at:   {m.get('created_at') or '-'}",
            f"  promoted_at:  {m.get('promoted_at') or '-'}",
            f"  source:       {m.get('source_transcript') or '-'}",
        ]
        if self.assertions is None:
            lines.append(f"  assertions:   (none — run `failpack promote {self.pack_id}`)")
            return lines

        lines.append("  assertions:")
        for item in self.assertion_summary:
            lines.append(f"    - {item}")
        return lines


def _normalize_contains_entries(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [{"contains": raw}]
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        out: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, str):
                out.append({"contains": item})
            elif isinstance(item, dict):
                out.append(item)
        return out
    return []


def _summarize_assertions(assertions: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if assertions.get("exit_code") is not None:
        items.append(f"exit_code == {assertions['exit_code']}")
    if assertions.get("min_events") is not None:
        items.append(f"min_events >= {assertions['min_events']}")
    fps = assertions.get("fingerprints") or []
    if fps:
        items.append(f"{len(fps)} fingerprint(s)")
    globs = assertions.get("glob_fingerprint") or assertions.get("glob_fingerprints") or []
    if isinstance(globs, dict):
        globs = [globs]
    if globs:
        for g in globs:
            pattern = g.get("pattern") or g.get("glob") or "?"
            items.append(f"glob_fingerprint:{pattern}")
    subs = assertions.get("substrings") or []
    if subs:
        items.append(f"{len(subs)} substring(s)")
    for entry in _normalize_contains_entries(assertions.get("tool_denied_contains")):
        needle = entry.get("contains") or "?"
        items.append(f"tool_denied_contains:{needle}")
    for entry in _normalize_contains_entries(assertions.get("bash_output_contains")):
        needle = entry.get("contains") or "?"
        match = entry.get("match") or entry.get("which") or "any"
        suffix = f" ({match})" if match != "any" else ""
        items.append(f"bash_output_contains:{needle}{suffix}")
    if not items:
        items.append("(empty assertions.yaml)")
    return items


def cmd_status(pack_id: str, *, root: Path | None = None) -> StatusReport:
    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    assertions: dict[str, Any] | None = None
    summary: list[str] = []
    if (pack / ASSERTIONS_NAME).is_file():
        assertions = read_assertions(pack)
        summary = _summarize_assertions(assertions)
    return StatusReport(
        pack_id=pack_id,
        meta=meta,
        assertions=assertions,
        assertion_summary=summary,
    )
