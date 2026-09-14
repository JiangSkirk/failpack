"""failpack replay — verify golden assertions against pack artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from failpack.color import paint, use_color
from failpack.commands_list import list_packs
from failpack.diffutil import fingerprint_diff
from failpack.events import bash_output_contains, load_pack_events, tool_denied_contains
from failpack.pack import artifacts_dir, glob_fingerprint, read_assertions, read_meta, sha256_file
from failpack.paths import TRANSCRIPT_NAME, failpack_dir, require_pack


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    expected: str | None = None
    actual: str | None = None
    hint: str | None = None
    diff: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


def _hint_for_check(name: str, *, missing: bool = False, kind: str = "") -> str:
    if missing:
        if name.startswith("fingerprint:") or name.startswith("substring:"):
            path = name.split(":", 1)[1]
            return f"artifact missing — inspect {path}"
        if name == "exit_code":
            return "artifact missing — inspect artifacts/exit_code.txt"
        if name == "min_events":
            return "meta.event_count missing — re-capture the session"
        return "inspect pack layout under .failpack/packs/"
    if name == "exit_code":
        return "re-promote after intentional change"
    if name == "min_events":
        return "session shorter than golden — re-capture or lower min_events"
    if name.startswith("fingerprint:"):
        path = name.split(":", 1)[1]
        return f"artifact drifted — inspect {path}"
    if name.startswith("glob_fingerprint:"):
        return "written files drifted — inspect artifacts/files/"
    if name.startswith("substring:"):
        return "re-promote after intentional change"
    if name.startswith("tool_denied_contains:"):
        return "denied tool signal missing — inspect transcript.jsonl tool_result events"
    if name.startswith("bash_output_contains:"):
        return "Bash output signal missing — inspect Bash tool_result events in transcript"
    if name == "assertions":
        return "run failpack promote <id> to write assertions.yaml"
    if kind == "file_count":
        return "written file set drifted — inspect artifacts/files/"
    return "inspect pack artifacts and re-promote if the change is intentional"


def _normalize_contains_entries(raw: Any) -> list[dict[str, Any]]:
    """Normalize list/dict/string assertion entries into ``{contains, ...}`` dicts."""
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


def _what_broke(check: CheckResult) -> str:
    """Plain-English one-liner for a failed check."""
    name = check.name
    if name == "exit_code":
        return (
            f"session exit code drifted "
            f"(expected {check.expected}, got {check.actual})"
        )
    if name == "min_events":
        return f"session event count too low ({check.detail})"
    if name.startswith("fingerprint:"):
        path = name.split(":", 1)[1]
        return f"artifact fingerprint drifted for {path}"
    if name.startswith("glob_fingerprint:"):
        pattern = name.split(":", 1)[1]
        return f"written-file set drifted (glob {pattern})"
    if name.startswith("substring:"):
        path = name.split(":", 1)[1]
        return f"expected error/signal text missing in {path}"
    if name.startswith("tool_denied_contains:"):
        needle = name.split(":", 1)[1]
        return f"denied-tool signal missing (looking for {needle!r})"
    if name.startswith("bash_output_contains:"):
        needle = name.split(":", 1)[1]
        return f"Bash output signal missing (looking for {needle!r})"
    if name == "assertions":
        return "no assertions defined for this pack"
    return check.detail or name


def _next_step(check: CheckResult, pack_id: str) -> str:
    """Actionable next step for a failed check."""
    if check.hint:
        hint = check.hint
        if "re-promote" in hint:
            return (
                f"restore the golden signal, or run `failpack re-promote {pack_id}` "
                "if the change is intentional"
            )
        if "artifact drifted" in hint or "artifact missing" in hint:
            return (
                f"{hint}; restore the file, or `failpack re-promote {pack_id}` "
                "if the new content is the new golden"
            )
        if "denied tool" in hint or "Bash output" in hint:
            return (
                f"{hint}; or `failpack re-promote {pack_id}` after intentional "
                "transcript changes"
            )
        return hint
    return (
        f"inspect `.failpack/packs/{pack_id}/`, then restore or "
        f"`failpack re-promote {pack_id}`"
    )


@dataclass
class ReplayReport:
    pack_id: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks) and bool(self.checks)

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.ok]

    def story_lines(self) -> list[str]:
        """One coherent short narrative for humans (PASS or FAIL)."""
        if self.ok:
            n = len(self.checks)
            return [
                f"STORY: Pack '{self.pack_id}' passed all {n} check"
                f"{'s' if n != 1 else ''}.",
                "  Nothing to fix — golden regression memory is intact.",
            ]

        failed = self.failed_checks
        primary = failed[0]
        lines = [
            f"STORY: Pack '{self.pack_id}' failed "
            f"{len(failed)} of {len(self.checks)} check"
            f"{'s' if len(self.checks) != 1 else ''}.",
            f"  What broke: {_what_broke(primary)}",
            f"  Assertion:  {primary.name}",
            f"  Next:       {_next_step(primary, self.pack_id)}",
        ]
        if len(failed) > 1:
            others = ", ".join(c.name for c in failed[1:])
            lines.append(f"  Also failed: {others}")
        return lines

    def summary_lines(self, *, color: bool | None = None) -> list[str]:
        enabled = use_color() if color is None else color
        lines = [f"failpack replay: {self.pack_id}"]
        for c in self.checks:
            mark = "PASS" if c.ok else "FAIL"
            colored = paint(mark, "green" if c.ok else "red", enabled=enabled)
            lines.append(f"  [{colored}] {c.name}: {c.detail}")
            if not c.ok:
                if c.expected is not None:
                    lines.append(f"         expected: {c.expected}")
                if c.actual is not None:
                    lines.append(f"         actual:   {c.actual}")
                if c.hint:
                    lines.append(f"         hint:     {c.hint}")
                if c.diff:
                    lines.append("         diff:")
                    for dline in c.diff.splitlines():
                        lines.append(f"           {dline}")
        if not self.ok:
            lines.append("")
            lines.extend(self.story_lines())
        result = "PASS" if self.ok else "FAIL"
        lines.append(
            "RESULT: " + paint(result, "green" if self.ok else "red", enabled=enabled)
        )
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "ok": self.ok,
            "checks": [c.to_dict() for c in self.checks],
            "story": self.story_lines(),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent) + "\n"


@dataclass
class ReplayAllReport:
    reports: list[ReplayReport] = field(default_factory=list)
    skipped_non_golden: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        # No golden packs → success (nothing to fail). Any failed pack → fail.
        return all(r.ok for r in self.reports)

    def summary_lines(self, *, color: bool | None = None) -> list[str]:
        enabled = use_color() if color is None else color
        lines = ["failpack replay --all"]
        if not self.reports:
            lines.append("  (no golden packs found)")
            lines.append("RESULT: " + paint("PASS", "green", enabled=enabled))
            return lines
        for report in self.reports:
            mark = "PASS" if report.ok else "FAIL"
            colored = paint(mark, "green" if report.ok else "red", enabled=enabled)
            lines.append(f"  [{colored}] {report.pack_id}")
            for c in report.checks:
                cmark = "PASS" if c.ok else "FAIL"
                ccolored = paint(cmark, "green" if c.ok else "red", enabled=enabled)
                lines.append(f"    [{ccolored}] {c.name}: {c.detail}")
                if not c.ok:
                    if c.expected is not None:
                        lines.append(f"           expected: {c.expected}")
                    if c.actual is not None:
                        lines.append(f"           actual:   {c.actual}")
                    if c.hint:
                        lines.append(f"           hint:     {c.hint}")
                    if c.diff:
                        lines.append("           diff:")
                        for dline in c.diff.splitlines():
                            lines.append(f"             {dline}")
        passed = sum(1 for r in self.reports if r.ok)
        failed = [r.pack_id for r in self.reports if not r.ok]
        total = len(self.reports)
        lines.append(
            f"SUMMARY: {passed} passed, {len(failed)} failed "
            f"({total} golden pack{'s' if total != 1 else ''})"
        )
        if failed:
            lines.append("  failed packs: " + ", ".join(failed))
            lines.append("  tip: failpack explain <id>  # short narrative for a FAIL")
            lines.append("  tip: failpack re-promote <id> after intentional fixes")
            # One coherent story per failed pack (keeps --all readable)
            for report in self.reports:
                if report.ok:
                    continue
                lines.append("")
                lines.extend(report.story_lines())
        result = "PASS" if self.ok else "FAIL"
        lines.append(
            "RESULT: "
            + paint(result, "green" if self.ok else "red", enabled=enabled)
            + f" ({passed}/{total} golden packs passed)"
        )
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "skipped_non_golden": list(self.skipped_non_golden),
            "packs": [r.to_dict() for r in self.reports],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent) + "\n"


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


def cmd_replay(
    pack_id: str,
    *,
    root: Path | None = None,
    show_diff: bool = True,
) -> ReplayReport:
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
                CheckResult(
                    "exit_code",
                    False,
                    f"missing {exit_path.name}",
                    expected=str(expected_exit),
                    actual="(missing)",
                    hint=_hint_for_check("exit_code", missing=True),
                )
            )
        else:
            actual = int(exit_path.read_text(encoding="utf-8").strip())
            ok = actual == int(expected_exit)
            report.checks.append(
                CheckResult(
                    "exit_code",
                    ok,
                    f"expected {expected_exit}, got {actual}",
                    expected=str(expected_exit),
                    actual=str(actual),
                    hint=None if ok else _hint_for_check("exit_code"),
                )
            )

    # min_events (optional, backward compatible)
    min_events = assertions.get("min_events")
    if min_events is not None:
        actual_events = meta.get("event_count")
        if actual_events is None:
            report.checks.append(
                CheckResult(
                    "min_events",
                    False,
                    "meta.event_count missing",
                    expected=f">= {min_events}",
                    actual="(missing)",
                    hint=_hint_for_check("min_events", missing=True),
                )
            )
        else:
            ok = int(actual_events) >= int(min_events)
            report.checks.append(
                CheckResult(
                    "min_events",
                    ok,
                    f"expected >= {min_events}, got {actual_events}",
                    expected=f">= {min_events}",
                    actual=str(actual_events),
                    hint=None if ok else _hint_for_check("min_events"),
                )
            )

    # fingerprint checks
    for fp in assertions.get("fingerprints") or []:
        rel = fp["path"]
        expected = fp["sha256"]
        path = pack / rel
        name = f"fingerprint:{rel}"
        if not path.is_file():
            report.checks.append(
                CheckResult(
                    name,
                    False,
                    "file missing",
                    expected=expected,
                    actual="(missing)",
                    hint=_hint_for_check(name, missing=True),
                )
            )
            continue
        actual = sha256_file(path)
        ok = actual == expected
        detail = "match" if ok else f"expected {expected[:12]}… got {actual[:12]}…"
        diff_text = None
        if not ok and show_diff:
            diff_text = fingerprint_diff(pack, rel)
        report.checks.append(
            CheckResult(
                name,
                ok,
                detail,
                expected=expected if not ok else None,
                actual=actual if not ok else None,
                hint=None if ok else _hint_for_check(name),
                diff=diff_text,
            )
        )

    # glob_fingerprint checks (optional)
    for entry in _normalize_glob_entries(assertions):
        pattern = entry.get("pattern") or entry.get("glob") or ""
        expected = entry.get("sha256") or ""
        name = f"glob_fingerprint:{pattern}"
        if not pattern or not expected:
            report.checks.append(
                CheckResult(
                    name,
                    False,
                    "incomplete glob_fingerprint entry",
                    hint="fix assertions.yaml glob_fingerprint (pattern + sha256)",
                )
            )
            continue
        actual, matched = glob_fingerprint(pack, pattern)
        expected_count = entry.get("file_count")
        if expected_count is not None and len(matched) != int(expected_count):
            report.checks.append(
                CheckResult(
                    name,
                    False,
                    f"file_count expected {expected_count}, got {len(matched)}",
                    expected=f"{expected_count} files",
                    actual=f"{len(matched)} files",
                    hint=_hint_for_check(name, kind="file_count"),
                )
            )
            continue
        ok = actual == expected
        detail = (
            f"match ({len(matched)} files)"
            if ok
            else f"expected {expected[:12]}… got {actual[:12]}… ({len(matched)} files)"
        )
        report.checks.append(
            CheckResult(
                name,
                ok,
                detail,
                expected=expected if not ok else None,
                actual=actual if not ok else None,
                hint=None if ok else _hint_for_check(name),
            )
        )

    # substring checks
    for sub in assertions.get("substrings") or []:
        rel = sub["path"]
        needle = sub["contains"]
        path = pack / rel
        name = f"substring:{rel}"
        if not path.is_file():
            report.checks.append(
                CheckResult(
                    name,
                    False,
                    "file missing",
                    expected=repr(needle),
                    actual="(missing)",
                    hint=_hint_for_check(name, missing=True),
                )
            )
            continue
        text = path.read_text(encoding="utf-8")
        ok = needle in text
        detail = "found" if ok else f"missing expected text: {needle!r}"
        report.checks.append(
            CheckResult(
                name,
                ok,
                detail,
                expected=f"contains {needle!r}" if not ok else None,
                actual="not found" if not ok else None,
                hint=None if ok else _hint_for_check(name),
            )
        )

    # Transcript-based asserts (optional; older packs omit these)
    tool_denied_entries = _normalize_contains_entries(
        assertions.get("tool_denied_contains")
    )
    bash_output_entries = _normalize_contains_entries(
        assertions.get("bash_output_contains")
    )
    events: list[dict[str, Any]] | None = None
    if tool_denied_entries or bash_output_entries:
        transcript = pack / TRANSCRIPT_NAME
        if not transcript.is_file():
            for entry in tool_denied_entries:
                needle = str(entry.get("contains") or "")
                report.checks.append(
                    CheckResult(
                        f"tool_denied_contains:{needle}",
                        False,
                        "transcript.jsonl missing",
                        expected=f"denied tool name contains {needle!r}",
                        actual="(missing transcript)",
                        hint=_hint_for_check(f"tool_denied_contains:{needle}", missing=True),
                    )
                )
            for entry in bash_output_entries:
                needle = str(entry.get("contains") or "")
                report.checks.append(
                    CheckResult(
                        f"bash_output_contains:{needle}",
                        False,
                        "transcript.jsonl missing",
                        expected=f"Bash output contains {needle!r}",
                        actual="(missing transcript)",
                        hint=_hint_for_check(f"bash_output_contains:{needle}", missing=True),
                    )
                )
        else:
            events = load_pack_events(transcript)

    if events is not None:
        for entry in tool_denied_entries:
            needle = str(entry.get("contains") or "")
            name = f"tool_denied_contains:{needle}"
            if not needle:
                report.checks.append(
                    CheckResult(
                        name,
                        False,
                        "incomplete tool_denied_contains entry (needs contains)",
                        hint="fix assertions.yaml tool_denied_contains",
                    )
                )
                continue
            ok = tool_denied_contains(events, needle)
            detail = "found" if ok else f"no denied tool name contains {needle!r}"
            report.checks.append(
                CheckResult(
                    name,
                    ok,
                    detail,
                    expected=f"denied tool name contains {needle!r}" if not ok else None,
                    actual="not found" if not ok else None,
                    hint=None if ok else _hint_for_check(name),
                )
            )

        for entry in bash_output_entries:
            needle = str(entry.get("contains") or "")
            match_mode = str(entry.get("match") or entry.get("which") or "any")
            name = f"bash_output_contains:{needle}"
            if not needle:
                report.checks.append(
                    CheckResult(
                        name,
                        False,
                        "incomplete bash_output_contains entry (needs contains)",
                        hint="fix assertions.yaml bash_output_contains",
                    )
                )
                continue
            ok = bash_output_contains(events, needle, match=match_mode)
            detail = (
                f"found ({match_mode})"
                if ok
                else f"Bash output ({match_mode}) missing {needle!r}"
            )
            report.checks.append(
                CheckResult(
                    name,
                    ok,
                    detail,
                    expected=(
                        f"Bash output ({match_mode}) contains {needle!r}"
                        if not ok
                        else None
                    ),
                    actual="not found" if not ok else None,
                    hint=None if ok else _hint_for_check(name),
                )
            )

    if not report.checks:
        report.checks.append(
            CheckResult(
                "assertions",
                False,
                "no checks defined in assertions.yaml",
                hint=_hint_for_check("assertions"),
            )
        )

    return report


def cmd_replay_all(
    *,
    root: Path | None = None,
    show_diff: bool = True,
) -> ReplayAllReport:
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
        all_report.reports.append(cmd_replay(row.id, root=root, show_diff=show_diff))
    return all_report
