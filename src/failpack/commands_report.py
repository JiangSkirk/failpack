"""failpack report — markdown replay summary (GitHub Actions step summary)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from failpack.commands_replay import ReplayAllReport, ReplayReport, cmd_replay, cmd_replay_all


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_report_markdown(
    report: ReplayReport | ReplayAllReport,
    *,
    title: str = "FailPack replay",
) -> str:
    """Render a GitHub-flavored markdown summary for CI step summaries."""
    lines: list[str] = [f"# {title}", ""]

    if isinstance(report, ReplayReport):
        all_report = ReplayAllReport(reports=[report])
    else:
        all_report = report

    if not all_report.reports:
        lines.append("_No golden packs found._")
        lines.append("")
        lines.append("**RESULT: PASS**")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Pack | Result | Checks |")
    lines.append("| --- | --- | --- |")
    for r in all_report.reports:
        passed = sum(1 for c in r.checks if c.ok)
        total = len(r.checks)
        mark = "PASS" if r.ok else "FAIL"
        lines.append(
            f"| `{_md_escape(r.pack_id)}` | **{mark}** | {passed}/{total} |"
        )
    lines.append("")

    failed = [r for r in all_report.reports if not r.ok]
    if failed:
        lines.append("## Failures")
        lines.append("")
        for r in failed:
            lines.append(f"### `{_md_escape(r.pack_id)}`")
            lines.append("")
            for c in r.checks:
                if c.ok:
                    continue
                lines.append(f"- **FAIL** `{_md_escape(c.name)}`: {_md_escape(c.detail)}")
                if c.expected is not None:
                    lines.append(f"  - expected: `{_md_escape(str(c.expected))}`")
                if c.actual is not None:
                    lines.append(f"  - actual: `{_md_escape(str(c.actual))}`")
                if c.hint:
                    lines.append(f"  - hint: {_md_escape(c.hint)}")
                if c.diff:
                    lines.append("  - diff:")
                    lines.append("")
                    lines.append("```diff")
                    # Cap diff size for step-summary readability
                    diff_lines = c.diff.splitlines()[:40]
                    lines.extend(diff_lines)
                    if len(c.diff.splitlines()) > 40:
                        lines.append("… (truncated)")
                    lines.append("```")
            lines.append("")
        lines.append(
            "_Tip: `failpack re-promote <id>` after intentional fixes._"
        )
        lines.append("")

    passed_n = sum(1 for r in all_report.reports if r.ok)
    total_n = len(all_report.reports)
    result = "PASS" if all_report.ok else "FAIL"
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"**RESULT: {result}** — {passed_n}/{total_n} golden pack"
        f"{'s' if total_n != 1 else ''} passed"
    )
    if all_report.skipped_non_golden:
        skipped = ", ".join(f"`{s}`" for s in all_report.skipped_non_golden)
        lines.append("")
        lines.append(f"_Skipped non-golden: {skipped}_")
    lines.append("")
    return "\n".join(lines)


@dataclass
class ReportResult:
    markdown: str
    ok: bool
    written_to: Path | None = None
    lines: list[str] = field(default_factory=list)

    def summary_lines(self) -> list[str]:
        if self.lines:
            return list(self.lines)
        result = "PASS" if self.ok else "FAIL"
        out = [f"failpack report: {result}"]
        if self.written_to is not None:
            out.append(f"  wrote step summary → {self.written_to}")
        return out


def cmd_report(
    pack_id: str | None = None,
    *,
    root: Path | None = None,
    github: bool = False,
    output: Path | None = None,
    show_diff: bool = True,
) -> ReportResult:
    """Build a markdown replay report.

    When *github* is True, append markdown to ``$GITHUB_STEP_SUMMARY``
    (required in GitHub Actions). Otherwise write to *output* if given, else
    the markdown is returned for the caller to print to stdout.
    """
    if pack_id:
        report: ReplayReport | ReplayAllReport = cmd_replay(
            pack_id, root=root, show_diff=show_diff
        )
        title = f"FailPack replay: {pack_id}"
    else:
        report = cmd_replay_all(root=root, show_diff=show_diff)
        title = "FailPack replay"

    markdown = render_report_markdown(report, title=title)
    written: Path | None = None
    notes: list[str] = []

    if github:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_path:
            raise ValueError(
                "--github requires $GITHUB_STEP_SUMMARY "
                "(set automatically in GitHub Actions)."
            )
        path = Path(summary_path)
        with path.open("a", encoding="utf-8") as f:
            f.write(markdown)
            if not markdown.endswith("\n"):
                f.write("\n")
        written = path
        notes.append(f"failpack report: {'PASS' if report.ok else 'FAIL'}")
        notes.append(f"  wrote step summary → {path}")
    elif output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        written = output
        notes.append(f"failpack report: {'PASS' if report.ok else 'FAIL'}")
        notes.append(f"  wrote → {output}")

    return ReportResult(
        markdown=markdown,
        ok=report.ok,
        written_to=written,
        lines=notes,
    )
