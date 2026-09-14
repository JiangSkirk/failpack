"""failpack show — pretty inspect one pack (status, asserts, artifacts)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from failpack.color import paint, use_color
from failpack.commands_status import _summarize_assertions
from failpack.pack import artifacts_dir, read_assertions, read_meta
from failpack.paths import ASSERTIONS_NAME, require_pack


def list_artifact_paths(pack: Path) -> list[str]:
    """Return pack-relative artifact file paths, sorted."""
    arts = artifacts_dir(pack)
    if not arts.is_dir():
        return []
    out: list[str] = []
    for path in sorted(arts.rglob("*")):
        if path.is_file():
            out.append(path.relative_to(pack).as_posix())
    return out


@dataclass
class ShowReport:
    pack_id: str
    meta: dict[str, Any]
    assertions: dict[str, Any] | None = None
    assertion_summary: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    def summary_lines(self, *, color: bool | None = None) -> list[str]:
        enabled = use_color() if color is None else color
        m = self.meta
        status = str(m.get("status") or "unknown")
        status_colored = paint(
            status,
            "green" if status == "golden" else "yellow" if status == "captured" else "dim",
            enabled=enabled,
        )
        title = paint(f"failpack show: {self.pack_id}", "bold", enabled=enabled)
        lines = [
            title,
            f"  status:       {status_colored}",
            f"  exit_code:    {m.get('exit_code', '-')}",
            f"  promoted_at:  {m.get('promoted_at') or '-'}",
            f"  events:       {m.get('event_count', '-')}",
            f"  schema:       {m.get('schema_version', '(unset)')}",
            f"  session_id:   {m.get('session_id') or '-'}",
            f"  created_at:   {m.get('created_at') or '-'}",
            f"  source:       {m.get('source_transcript') or '-'}",
        ]

        lines.append("  assertions:")
        if self.assertions is None:
            lines.append(
                f"    (none — run `failpack promote {self.pack_id}`)"
            )
        elif not self.assertion_summary:
            lines.append("    (empty assertions.yaml)")
        else:
            for item in self.assertion_summary:
                lines.append(f"    - {item}")

        lines.append(f"  artifacts:    ({len(self.artifacts)})")
        if not self.artifacts:
            lines.append("    (none)")
        else:
            for rel in self.artifacts:
                lines.append(f"    - {rel}")
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "status": self.meta.get("status"),
            "exit_code": self.meta.get("exit_code"),
            "promoted_at": self.meta.get("promoted_at"),
            "event_count": self.meta.get("event_count"),
            "schema_version": self.meta.get("schema_version"),
            "session_id": self.meta.get("session_id"),
            "created_at": self.meta.get("created_at"),
            "source_transcript": self.meta.get("source_transcript"),
            "meta": self.meta,
            "assertions": self.assertions,
            "assertion_summary": list(self.assertion_summary),
            "artifacts": list(self.artifacts),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent) + "\n"


def cmd_show(pack_id: str, *, root: Path | None = None) -> ShowReport:
    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    assertions: dict[str, Any] | None = None
    summary: list[str] = []
    if (pack / ASSERTIONS_NAME).is_file():
        assertions = read_assertions(pack)
        summary = _summarize_assertions(assertions)
    return ShowReport(
        pack_id=pack_id,
        meta=meta,
        assertions=assertions,
        assertion_summary=summary,
        artifacts=list_artifact_paths(pack),
    )
