"""failpack migrate — bump pack schema_version (stub; no-op when current)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from failpack.commands_list import list_packs
from failpack.diffutil import write_expected_snapshot
from failpack.pack import read_assertions, read_meta, write_meta
from failpack.paths import failpack_dir, require_pack
from failpack.schema import (
    CURRENT_SCHEMA_VERSION,
    schema_version_of,
    with_current_schema,
)


@dataclass
class MigrateReport:
    current_version: int = CURRENT_SCHEMA_VERSION
    migrated: list[str] = field(default_factory=list)
    already_current: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    message: str = ""

    @property
    def ok(self) -> bool:
        return True

    def summary_lines(self) -> list[str]:
        lines = [f"failpack migrate (schema v{self.current_version})"]
        if self.message:
            lines.append(f"  {self.message}")
        if self.migrated:
            lines.append(f"  migrated: {', '.join(self.migrated)}")
        if self.already_current and not self.migrated:
            # Keep the happy path quiet — one line is enough.
            pass
        if self.skipped:
            lines.append(f"  skipped:  {', '.join(self.skipped)}")
        return lines


def _ensure_expected_snapshots(pack: Path) -> None:
    """Backfill ``expected/`` text snapshots from fingerprints when missing."""
    try:
        assertions = read_assertions(pack)
    except FileNotFoundError:
        return
    for fp in assertions.get("fingerprints") or []:
        rel = fp.get("path")
        if not rel:
            continue
        source = pack / rel
        dest = pack / "expected" / rel
        if dest.is_file():
            continue
        write_expected_snapshot(pack, rel, source)


def migrate_pack(pack_id: str, *, root: Path | None = None) -> str:
    """Migrate one pack to the current schema. Returns status label."""
    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    ver = schema_version_of(meta)
    if ver >= CURRENT_SCHEMA_VERSION:
        _ensure_expected_snapshots(pack)
        return "current"
    write_meta(pack, with_current_schema(meta))
    _ensure_expected_snapshots(pack)
    return "migrated"


def cmd_migrate(*, root: Path | None = None) -> MigrateReport:
    """Migrate all packs under ``.failpack/packs/`` to the current schema.

    Forward-looking polish: today this only stamps ``schema_version`` and
    backfills ``expected/`` text snapshots used by diff-aware explain.
    When already current, prints a no-op message and exits 0.
    """
    base = failpack_dir(root)
    report = MigrateReport()
    if not base.is_dir():
        raise FileNotFoundError(
            f"No {base.name}/ directory. Run `failpack init` first."
        )

    rows = list_packs(root)
    if not rows:
        report.message = (
            f"no packs found — schema is current (v{CURRENT_SCHEMA_VERSION})"
        )
        return report

    for row in rows:
        status = migrate_pack(row.id, root=root)
        if status == "migrated":
            report.migrated.append(row.id)
        else:
            report.already_current.append(row.id)

    if not report.migrated:
        report.message = (
            f"already at schema version {CURRENT_SCHEMA_VERSION} "
            f"({len(report.already_current)} packs) — nothing to do"
        )
    else:
        report.message = (
            f"updated {len(report.migrated)} pack(s) to schema version "
            f"{CURRENT_SCHEMA_VERSION}"
        )
    return report
