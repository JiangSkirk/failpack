"""failpack explain — short narrative for a replay FAIL."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from failpack.commands_replay import (
    ReplayAllReport,
    ReplayReport,
    cmd_replay,
    cmd_replay_all,
)


@dataclass
class ExplainReport:
    reports: list[ReplayReport] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        # Mirror replay: no golden packs → success; any FAIL → non-zero.
        return all(r.ok for r in self.reports)

    def summary_lines(self) -> list[str]:
        return list(self.lines)


def cmd_explain(
    pack_id: str | None = None,
    *,
    root: Path | None = None,
    show_diff: bool = False,
) -> ExplainReport:
    """Replay and print a coherent FAIL story (what / which assert / next).

    When *pack_id* is omitted, explain every golden pack that currently FAILs
    (or a short PASS note when all are green).
    """
    out = ExplainReport()

    if pack_id:
        report = cmd_replay(pack_id, root=root, show_diff=show_diff)
        out.reports.append(report)
        out.lines.append(f"failpack explain: {pack_id}")
        out.lines.extend(report.story_lines())
        if not report.ok and report.failed_checks:
            primary = report.failed_checks[0]
            if primary.expected is not None:
                out.lines.append(f"  expected:   {primary.expected}")
            if primary.actual is not None:
                out.lines.append(f"  actual:     {primary.actual}")
        out.lines.append(f"RESULT: {'PASS' if report.ok else 'FAIL'}")
        if not report.ok:
            out.lines.append(
                f"next: failpack promote --suggest {pack_id}  ·  "
                f"failpack re-promote {pack_id}"
            )
        return out

    all_report: ReplayAllReport = cmd_replay_all(root=root, show_diff=show_diff)
    out.reports.extend(all_report.reports)
    failed = [r for r in all_report.reports if not r.ok]

    out.lines.append("failpack explain")
    if not all_report.reports:
        out.lines.append("  (no golden packs found)")
        out.lines.append("RESULT: PASS")
        return out

    if not failed:
        out.lines.append(
            f"  All {len(all_report.reports)} golden pack"
            f"{'s' if len(all_report.reports) != 1 else ''} passed."
        )
        out.lines.append("RESULT: PASS")
        return out

    for report in failed:
        out.lines.append("")
        out.lines.extend(report.story_lines())
        primary = report.failed_checks[0] if report.failed_checks else None
        if primary is not None:
            if primary.expected is not None:
                out.lines.append(f"  expected:   {primary.expected}")
            if primary.actual is not None:
                out.lines.append(f"  actual:     {primary.actual}")

    out.lines.append("")
    out.lines.append(
        f"RESULT: FAIL ({len(failed)}/{len(all_report.reports)} golden packs failed)"
    )
    first_id = failed[0].pack_id
    out.lines.append(
        f"next: failpack promote --suggest {first_id}  ·  "
        f"failpack re-promote {first_id}"
    )
    return out
