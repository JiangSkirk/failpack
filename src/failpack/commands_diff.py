"""failpack diff — expected vs actual artifact summary (no full replay)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from failpack.color import paint, use_color
from failpack.diffutil import fingerprint_diff, read_text_for_diff
from failpack.paths import require_pack

EXPECTED_DIR = "expected"


@dataclass
class DiffFile:
    rel: str
    status: str  # match | differ | missing_actual | missing_expected | unreadable
    diff: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"path": self.rel, "status": self.status}
        if self.diff is not None:
            out["diff"] = self.diff
        return out


@dataclass
class DiffReport:
    pack_id: str
    files: list[DiffFile] = field(default_factory=list)
    note: str | None = None

    @property
    def ok(self) -> bool:
        if self.note and not self.files:
            return False
        return all(f.status == "match" for f in self.files)

    @property
    def matched(self) -> int:
        return sum(1 for f in self.files if f.status == "match")

    @property
    def differed(self) -> int:
        return sum(1 for f in self.files if f.status != "match")

    def summary_lines(
        self,
        *,
        show_diff: bool = True,
        color: bool | None = None,
    ) -> list[str]:
        enabled = use_color() if color is None else color
        title = paint(f"failpack diff: {self.pack_id}", "bold", enabled=enabled)
        lines = [title]

        if self.note and not self.files:
            lines.append(f"  {self.note}")
            lines.append(
                paint("RESULT: FAIL", "red", enabled=enabled)
                if not self.ok
                else paint("RESULT: PASS", "green", enabled=enabled)
            )
            return lines

        if not self.files:
            lines.append("  (no expected/ snapshots — nothing to compare)")
            lines.append(paint("RESULT: PASS", "green", enabled=enabled))
            return lines

        for item in self.files:
            if item.status == "match":
                mark = paint("[PASS]", "green", enabled=enabled)
                lines.append(f"  {mark} {item.rel}: match")
            elif item.status == "differ":
                mark = paint("[FAIL]", "red", enabled=enabled)
                lines.append(f"  {mark} {item.rel}: differ")
                if show_diff and item.diff:
                    lines.append("         diff:")
                    for dline in item.diff.splitlines():
                        lines.append(f"           {dline}")
            elif item.status == "missing_actual":
                mark = paint("[FAIL]", "red", enabled=enabled)
                lines.append(f"  {mark} {item.rel}: missing actual artifact")
            elif item.status == "missing_expected":
                mark = paint("[FAIL]", "red", enabled=enabled)
                lines.append(f"  {mark} {item.rel}: missing expected snapshot")
            else:
                mark = paint("[FAIL]", "red", enabled=enabled)
                lines.append(f"  {mark} {item.rel}: {item.status}")

        lines.append(
            f"  summary: {self.matched} match, {self.differed} differ "
            f"({len(self.files)} snapshot(s))"
        )
        result = (
            paint("RESULT: PASS", "green", enabled=enabled)
            if self.ok
            else paint("RESULT: FAIL", "red", enabled=enabled)
        )
        lines.append(result)
        if not self.ok:
            # Same order as replay/explain: RESULT first, then next: tip last.
            lines.append(
                f"next: failpack explain {self.pack_id}  ·  "
                f"failpack re-promote {self.pack_id}  ·  "
                f"failpack promote --suggest {self.pack_id}"
            )
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "ok": self.ok,
            "matched": self.matched,
            "differed": self.differed,
            "note": self.note,
            "files": [f.to_dict() for f in self.files],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent) + "\n"


def _list_expected_rels(pack: Path) -> list[str]:
    expected = pack / EXPECTED_DIR
    if not expected.is_dir():
        return []
    out: list[str] = []
    for path in sorted(expected.rglob("*")):
        if path.is_file():
            out.append(path.relative_to(expected).as_posix())
    return out


def cmd_diff(
    pack_id: str,
    *,
    root: Path | None = None,
    show_diff: bool = True,
) -> DiffReport:
    """Compare ``expected/`` snapshots to current artifacts — no assertion replay."""
    pack = require_pack(pack_id, root)
    expected_root = pack / EXPECTED_DIR
    if not expected_root.is_dir():
        return DiffReport(
            pack_id=pack_id,
            note=(
                f"no {EXPECTED_DIR}/ snapshots — run "
                f"`failpack promote {pack_id}` (or re-promote) first"
            ),
        )

    files: list[DiffFile] = []
    for rel in _list_expected_rels(pack):
        expected_path = expected_root / rel
        actual_path = pack / rel
        if not actual_path.is_file():
            files.append(DiffFile(rel=rel, status="missing_actual"))
            continue

        expected_text = read_text_for_diff(expected_path)
        actual_text = read_text_for_diff(actual_path)
        if expected_text is None or actual_text is None:
            # Fall back to byte equality for unreadable / binary-ish files.
            try:
                if expected_path.read_bytes() == actual_path.read_bytes():
                    files.append(DiffFile(rel=rel, status="match"))
                else:
                    files.append(DiffFile(rel=rel, status="differ"))
            except OSError:
                files.append(DiffFile(rel=rel, status="unreadable"))
            continue

        if expected_text == actual_text:
            files.append(DiffFile(rel=rel, status="match"))
            continue

        diff_text = fingerprint_diff(pack, rel) if show_diff else None
        files.append(DiffFile(rel=rel, status="differ", diff=diff_text))

    return DiffReport(pack_id=pack_id, files=files)
