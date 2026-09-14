"""failpack list — show packs under .failpack/packs/."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from failpack.pack import read_meta
from failpack.paths import failpack_dir, packs_dir

_HEADERS = ("ID", "STATUS", "EXIT", "PROMOTED_AT")


@dataclass
class PackRow:
    id: str
    status: str
    exit_code: int | None
    promoted_at: str | None

    def format_line(self) -> str:
        """Tab-separated row (machine-friendly / legacy)."""
        exit_s = "-" if self.exit_code is None else str(self.exit_code)
        promoted = self.promoted_at or "-"
        return f"{self.id}\t{self.status}\t{exit_s}\t{promoted}"

    def cells(self) -> tuple[str, str, str, str]:
        exit_s = "-" if self.exit_code is None else str(self.exit_code)
        promoted = self.promoted_at or "-"
        return (self.id, self.status, exit_s, promoted)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "exit_code": self.exit_code,
            "promoted_at": self.promoted_at,
        }


def format_table(rows: list[PackRow]) -> list[str]:
    """Progress-free aligned table for TTY / human output."""
    if not rows:
        return []
    cells = [row.cells() for row in rows]
    widths = [len(h) for h in _HEADERS]
    for row in cells:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(cols: tuple[str, ...]) -> str:
        return "  ".join(col.ljust(widths[i]) for i, col in enumerate(cols))

    lines = [fmt(_HEADERS), fmt(tuple("-" * w for w in widths))]
    lines.extend(fmt(row) for row in cells)
    return lines


def rows_to_json(rows: list[PackRow], *, indent: int = 2) -> str:
    """Stable machine-readable pack index for tooling."""
    return json.dumps([row.to_dict() for row in rows], indent=indent) + "\n"


def list_packs(root: Path | None = None) -> list[PackRow]:
    base = failpack_dir(root)
    if not base.is_dir():
        raise FileNotFoundError(
            f"No {base.name}/ directory. Run `failpack init` first."
        )
    packs = packs_dir(root)
    if not packs.is_dir():
        return []

    rows: list[PackRow] = []
    for path in sorted(packs.iterdir()):
        if not path.is_dir() or path.name.startswith("."):
            continue
        meta_path = path / "meta.json"
        if not meta_path.is_file():
            continue
        meta: dict[str, Any] = read_meta(path)
        exit_code = meta.get("exit_code")
        if exit_code is not None:
            exit_code = int(exit_code)
        rows.append(
            PackRow(
                id=str(meta.get("id") or path.name),
                status=str(meta.get("status") or "unknown"),
                exit_code=exit_code,
                promoted_at=meta.get("promoted_at"),
            )
        )
    return rows


def cmd_list(root: Path | None = None) -> list[PackRow]:
    return list_packs(root)
