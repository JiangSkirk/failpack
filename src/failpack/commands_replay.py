"""failpack replay — verify golden assertions against pack artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from failpack.commands_list import list_packs
from failpack.pack import artifacts_dir, glob_fingerprint, read_assertions, read_meta, sha256_file
from failpack.paths import failpack_dir, require_pack


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


@dataclass
class ReplayReport:
    pack_id: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks) and bool(self.checks)

    def summary_lines(self) -> list[str]:
        lines = [f"failpack replay: {self.pack_id}"]
        for c in self.checks:
            mark = "PASS" if c.ok else "FAIL"
            lines.append(f"  [{mark}] {c.name}: {c.detail}")
        lines.append("RESULT: " + ("PASS" if self.ok else "FAIL"))
        return lines


@dataclass
class ReplayAllReport:
    reports: list[ReplayReport] = field(default_factory=list)
    skipped_non_golden: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        # No golden packs → success (nothing to fail). Any failed pack → fail.
        return all(r.ok for r in self.reports)

    def summary_lines(self) -> list[str]:
        lines = ["failpack replay --all"]
        if not self.reports:
            lines.append("  (no golden packs found)")
            lines.append("RESULT: PASS")
            return lines
        for report in self.reports:
            mark = "PASS" if report.ok else "FAIL"
            lines.append(f"  [{mark}] {report.pack_id}")
            for c in report.checks:
                cmark = "PASS" if c.ok else "FAIL"
                lines.append(f"    [{cmark}] {c.name}: {c.detail}")
        failed = [r.pack_id for r in self.reports if not r.ok]
        lines.append(
            f"RESULT: {'PASS' if self.ok else 'FAIL'} "
            f"({len(self.reports) - len(failed)}/{len(self.reports)} golden packs passed)"
        )
        return lines


def _normalize_glob_entries(assertions: dict[str, Any]) -> list[dict[str, Any]]:
    raw = assertions.get("glob_fingerprint")
    if raw is None:
        raw = assertions.get("glob_fingerprints")
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [g for g in raw if isinstance(g, dict)]
    return []


def cmd_replay(pack_id: str, *, root: Path | None = None) -> ReplayReport:
    pack = require_pack(pack_id, root)
    meta = read_meta(pack)
    if meta.get("status") != "golden":
        # still allow replay if assertions exist (tests may mutate status)
        pass

    assertions = read_assertions(pack)
    report = ReplayReport(pack_id=pack_id)

    # exit code check
    expected_exit = assertions.get("exit_code")
    if expected_exit is not None:
        exit_path = artifacts_dir(pack) / "exit_code.txt"
        if not exit_path.is_file():
            report.checks.append(
                CheckResult("exit_code", False, f"missing {exit_path.name}")
            )
        else:
            actual = int(exit_path.read_text(encoding="utf-8").strip())
            ok = actual == int(expected_exit)
            report.checks.append(
                CheckResult(
                    "exit_code",
                    ok,
                    f"expected {expected_exit}, got {actual}",
                )
            )

    # min_events (optional, backward compatible)
    min_events = assertions.get("min_events")
    if min_events is not None:
        actual_events = meta.get("event_count")
        if actual_events is None:
            report.checks.append(
                CheckResult("min_events", False, "meta.event_count missing")
            )
        else:
            ok = int(actual_events) >= int(min_events)
            report.checks.append(
                CheckResult(
                    "min_events",
                    ok,
                    f"expected >= {min_events}, got {actual_events}",
                )
            )

    # fingerprint checks
    for fp in assertions.get("fingerprints") or []:
        rel = fp["path"]
        expected = fp["sha256"]
        path = pack / rel
        name = f"fingerprint:{rel}"
        if not path.is_file():
            report.checks.append(CheckResult(name, False, "file missing"))
            continue
        actual = sha256_file(path)
        ok = actual == expected
        detail = "match" if ok else f"expected {expected[:12]}… got {actual[:12]}…"
        report.checks.append(CheckResult(name, ok, detail))

    # glob_fingerprint checks (optional)
    for entry in _normalize_glob_entries(assertions):
        pattern = entry.get("pattern") or entry.get("glob") or ""
        expected = entry.get("sha256") or ""
        name = f"glob_fingerprint:{pattern}"
        if not pattern or not expected:
            report.checks.append(CheckResult(name, False, "incomplete glob_fingerprint entry"))
            continue
        actual, matched = glob_fingerprint(pack, pattern)
        expected_count = entry.get("file_count")
        if expected_count is not None and len(matched) != int(expected_count):
            report.checks.append(
                CheckResult(
                    name,
                    False,
                    f"file_count expected {expected_count}, got {len(matched)}",
                )
            )
            continue
        ok = actual == expected
        detail = (
            f"match ({len(matched)} files)"
            if ok
            else f"expected {expected[:12]}… got {actual[:12]}… ({len(matched)} files)"
        )
        report.checks.append(CheckResult(name, ok, detail))

    # substring checks
    for sub in assertions.get("substrings") or []:
        rel = sub["path"]
        needle = sub["contains"]
        path = pack / rel
        name = f"substring:{rel}"
        if not path.is_file():
            report.checks.append(CheckResult(name, False, "file missing"))
            continue
        text = path.read_text(encoding="utf-8")
        ok = needle in text
        detail = "found" if ok else f"missing expected text: {needle!r}"
        report.checks.append(CheckResult(name, ok, detail))

    if not report.checks:
        report.checks.append(
            CheckResult("assertions", False, "no checks defined in assertions.yaml")
        )

    return report


def cmd_replay_all(*, root: Path | None = None) -> ReplayAllReport:
    """Replay every golden pack under ``.failpack/packs/``."""
    base = failpack_dir(root)
    if not base.is_dir():
        raise FileNotFoundError(
            f"No {base.name}/ directory. Run `failpack init` first."
        )

    all_report = ReplayAllReport()
    for row in list_packs(root):
        if row.status != "golden":
            all_report.skipped_non_golden.append(row.id)
            continue
        all_report.reports.append(cmd_replay(row.id, root=root))
    return all_report
