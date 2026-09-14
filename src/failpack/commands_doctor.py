"""failpack doctor — environment and workspace health checks."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from failpack.commands_capture import claude_projects_dir, cursor_projects_dir
from failpack.commands_list import list_packs
from failpack.paths import FAILPACK_DIR, PACKS_DIR, failpack_dir, find_root


MIN_PYTHON = (3, 11)

# Readiness score weights (sum = 100). Checklist items for ``--score``.
# Agent paths (claude/cursor) are soft: missing either does not break CI —
# fixtures + ``failpack demo`` still reach 90/100.
SCORE_WEIGHTS: dict[str, int] = {
    "python": 25,
    "packs_dir": 25,
    "claude_projects": 5,
    "cursor_projects": 5,
    "lint": 20,
    "golden_count": 20,
}

GIT_INSTALL = 'pip install "git+https://github.com/JiangSkirk/failpack.git"'


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    detail: str
    fix: str | None = None
    # Optional points earned / max for --score checklist rows
    points: int | None = None
    max_points: int | None = None


@dataclass
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)
    score: int | None = None
    score_max: int = 100
    checklist: list[DoctorCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks) and bool(self.checks)

    def summary_lines(self, *, with_score: bool = False) -> list[str]:
        lines = ["failpack doctor"]
        for c in self.checks:
            mark = "OK" if c.ok else "FAIL"
            lines.append(f"  [{mark}] {c.name}: {c.detail}")
            if c.fix:
                label = "fix" if not c.ok else "tip"
                lines.append(f"         {label}: {c.fix}")

        if with_score and self.score is not None:
            lines.append("")
            lines.append(f"READINESS SCORE: {self.score}/{self.score_max}")
            lines.append("checklist:")
            for c in self.checklist:
                mark = "OK" if c.ok else "—"
                pts = ""
                if c.points is not None and c.max_points is not None:
                    pts = f"  (+{c.points}/{c.max_points})"
                lines.append(f"  [{mark}] {c.name}: {c.detail}{pts}")
                if c.fix and not c.ok:
                    lines.append(f"         fix: {c.fix}")

        lines.append("RESULT: " + ("OK" if self.ok else "FAIL"))
        return lines


def _check_python() -> DoctorCheck:
    ver = sys.version_info
    version_s = f"{ver.major}.{ver.minor}.{ver.micro}"
    ok = (ver.major, ver.minor) >= MIN_PYTHON
    need = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    if ok:
        return DoctorCheck("python", True, f"{version_s} (>= {need} required)")
    return DoctorCheck(
        "python",
        False,
        f"{version_s} (>= {need} required)",
        fix=(
            f"Install Python {need}+ and reinstall failpack "
            f'({GIT_INSTALL}).'
        ),
    )


def _check_pyyaml() -> DoctorCheck:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return DoctorCheck(
            "pyyaml",
            False,
            "not importable",
            fix="pip install 'pyyaml>=6.0'",
        )
    version = getattr(yaml, "__version__", "unknown")
    return DoctorCheck("pyyaml", True, f"importable (version {version})")


def _check_claude_projects(*, home: Path | None = None) -> DoctorCheck:
    """Report whether ``~/.claude/projects`` exists and how many sessions.

    Missing Claude Code is **not** a failure — FailPack works with fixtures.
    When sessions are found, tip the Claude one-shot ``capture --claude-latest``.
    """
    projects = claude_projects_dir(home=home)
    if not projects.is_dir():
        return DoctorCheck(
            "claude-projects",
            True,
            f"not found ({projects}) — optional",
            fix=(
                "After a Claude Code run: failpack capture --claude-latest --id my-failure  "
                "·  or ~60s wow: failpack demo --fast  ·  or: failpack capture --cursor-latest"
            ),
        )

    sessions = [p for p in projects.rglob("*.jsonl") if p.is_file()]
    n = len(sessions)
    if n == 0:
        return DoctorCheck(
            "claude-projects",
            True,
            f"found at {projects} (0 session *.jsonl)",
            fix=(
                "One-shot after your next Claude Code failure: "
                "failpack capture --claude-latest --id my-failure"
            ),
        )

    newest = max(sessions, key=lambda p: p.stat().st_mtime)
    return DoctorCheck(
        "claude-projects",
        True,
        f"found at {projects} ({n} session{'s' if n != 1 else ''})",
        fix=(
            f"One-shot: failpack capture --claude-latest --id my-failure  "
            f"(newest: {newest.name})"
        ),
    )


def _check_cursor_projects(*, home: Path | None = None) -> DoctorCheck:
    """Report whether ``~/.cursor/projects`` exists (soft / optional).

    Missing Cursor transcripts is **not** a failure — fixtures and Claude
    paths still work. When sessions are found, tip ``capture --cursor-latest``.
    """
    projects = cursor_projects_dir(home=home)
    if not projects.is_dir():
        return DoctorCheck(
            "cursor-projects",
            True,
            f"not found ({projects}) — optional",
            fix=(
                "Use Cursor agent transcripts, or capture a fixture / exported JSONL. "
                "Try: failpack demo · or: failpack capture --claude-latest"
            ),
        )

    sessions = [p for p in projects.rglob("*.jsonl") if p.is_file()]
    n = len(sessions)
    if n == 0:
        return DoctorCheck(
            "cursor-projects",
            True,
            f"found at {projects} (0 agent *.jsonl)",
            fix=(
                "After a Cursor agent run, try: "
                "failpack capture --cursor-latest --id my-failure"
            ),
        )

    newest = max(sessions, key=lambda p: p.stat().st_mtime)
    return DoctorCheck(
        "cursor-projects",
        True,
        f"found at {projects} ({n} transcript{'s' if n != 1 else ''})",
        fix=(
            f"Newest: {newest.name} — try: "
            "failpack capture --cursor-latest --id my-failure"
        ),
    )


def _check_layout(root: Path | None) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    project = find_root(root) if root is None else root.resolve()
    base = failpack_dir(project)

    if not base.is_dir():
        checks.append(
            DoctorCheck(
                "layout",
                False,
                f"no {FAILPACK_DIR}/ under {project}",
                fix=f"Run `failpack init` in {project} (or pass --root). Or: failpack demo",
            )
        )
        return checks

    packs = base / PACKS_DIR
    if not packs.is_dir():
        checks.append(
            DoctorCheck(
                "layout",
                False,
                f"{FAILPACK_DIR}/ found but missing {PACKS_DIR}/",
                fix=f"Run `failpack init` to create {FAILPACK_DIR}/{PACKS_DIR}/.",
            )
        )
        return checks

    checks.append(
        DoctorCheck(
            "layout",
            True,
            f"{FAILPACK_DIR}/ + {PACKS_DIR}/ at {base}",
        )
    )

    rows = list_packs(project)
    golden = sum(1 for r in rows if r.status == "golden")
    captured = sum(1 for r in rows if r.status == "captured")
    other = len(rows) - golden - captured
    detail = f"{len(rows)} pack(s) ({golden} golden, {captured} captured"
    if other:
        detail += f", {other} other"
    detail += ")"
    if not rows:
        checks.append(
            DoctorCheck(
                "packs",
                True,
                "0 packs — capture a transcript to get started",
                fix=(
                    "failpack demo --fast   # ~60s wow  ·  or: "
                    "failpack capture --claude-latest / --cursor-latest --id my-failure"
                ),
            )
        )
    else:
        checks.append(DoctorCheck("packs", True, detail))
    return checks


def _score_python(check: DoctorCheck) -> DoctorCheck:
    w = SCORE_WEIGHTS["python"]
    pts = w if check.ok else 0
    return DoctorCheck(
        "python",
        check.ok,
        check.detail,
        fix=check.fix,
        points=pts,
        max_points=w,
    )


def _score_packs_dir(root: Path | None) -> DoctorCheck:
    w = SCORE_WEIGHTS["packs_dir"]
    project = find_root(root) if root is None else root.resolve()
    packs = failpack_dir(project) / PACKS_DIR
    if packs.is_dir():
        return DoctorCheck(
            "packs_dir",
            True,
            f"{FAILPACK_DIR}/{PACKS_DIR}/ present",
            points=w,
            max_points=w,
        )
    return DoctorCheck(
        "packs_dir",
        False,
        f"missing {FAILPACK_DIR}/{PACKS_DIR}/",
        fix="Run `failpack init` (or `failpack demo`) to create the packs directory.",
        points=0,
        max_points=w,
    )


def _score_agent_projects(
    name: str,
    projects: Path,
    *,
    empty_fix: str,
    missing_fix: str,
) -> DoctorCheck:
    """Soft score row for an optional agent projects tree (Claude or Cursor)."""
    w = SCORE_WEIGHTS[name]
    if not projects.is_dir():
        return DoctorCheck(
            name,
            False,
            "not found (optional — fixtures / demo still work)",
            fix=missing_fix,
            points=0,
            max_points=w,
        )
    sessions = [p for p in projects.rglob("*.jsonl") if p.is_file()]
    n = len(sessions)
    if n == 0:
        # Directory exists but empty — half credit (floor at 1 when w>=2)
        half = max(1, w // 2) if w >= 2 else 0
        return DoctorCheck(
            name,
            True,
            f"found ({projects}) with 0 sessions",
            fix=empty_fix,
            points=half,
            max_points=w,
        )
    label = "session" if "claude" in name else "transcript"
    return DoctorCheck(
        name,
        True,
        f"found ({n} {label}{'s' if n != 1 else ''})",
        points=w,
        max_points=w,
    )


def _score_claude_projects(*, home: Path | None = None) -> DoctorCheck:
    return _score_agent_projects(
        "claude_projects",
        claude_projects_dir(home=home),
        empty_fix=(
            "One-shot: failpack capture --claude-latest --id my-failure"
        ),
        missing_fix="Install Claude Code, or skip: failpack demo --fast",
    )


def _score_cursor_projects(*, home: Path | None = None) -> DoctorCheck:
    return _score_agent_projects(
        "cursor_projects",
        cursor_projects_dir(home=home),
        empty_fix=(
            "After a Cursor agent run: failpack capture --cursor-latest --id my-failure"
        ),
        missing_fix="Use Cursor, or skip and use: failpack demo",
    )


def _score_lint(root: Path | None) -> DoctorCheck:
    w = SCORE_WEIGHTS["lint"]
    project = find_root(root) if root is None else root.resolve()
    packs = failpack_dir(project) / PACKS_DIR
    if not packs.is_dir():
        return DoctorCheck(
            "lint",
            False,
            "skipped — no packs dir",
            fix="Run `failpack init`, then `failpack lint`.",
            points=0,
            max_points=w,
        )
    from failpack.commands_lint import cmd_lint

    report = cmd_lint(None, root=project)
    if report.ok:
        n = len(report.checked)
        return DoctorCheck(
            "lint",
            True,
            f"PASS ({n} pack{'s' if n != 1 else ''} checked)",
            points=w,
            max_points=w,
        )
    errors = sum(1 for i in report.issues if i.level == "error")
    return DoctorCheck(
        "lint",
        False,
        f"FAIL ({errors} error(s))",
        fix="Run `failpack lint` and fix reported pack/assertion issues.",
        points=0,
        max_points=w,
    )


def _score_golden_count(root: Path | None) -> DoctorCheck:
    w = SCORE_WEIGHTS["golden_count"]
    project = find_root(root) if root is None else root.resolve()
    packs = failpack_dir(project) / PACKS_DIR
    if not packs.is_dir():
        return DoctorCheck(
            "golden_count",
            False,
            "0 golden (no packs dir)",
            fix="failpack demo   # or: capture → promote a pack",
            points=0,
            max_points=w,
        )
    rows = list_packs(project)
    golden = sum(1 for r in rows if r.status == "golden")
    if golden >= 1:
        return DoctorCheck(
            "golden_count",
            True,
            f"{golden} golden pack{'s' if golden != 1 else ''}",
            points=w,
            max_points=w,
        )
    return DoctorCheck(
        "golden_count",
        False,
        "0 golden packs",
        fix="failpack demo   # or: failpack promote <id> after capture",
        points=0,
        max_points=w,
    )


def compute_score(
    root: Path | None = None,
    *,
    home: Path | None = None,
    python_check: DoctorCheck | None = None,
) -> tuple[int, list[DoctorCheck]]:
    """Return (0–100 score, checklist rows) for readiness scoring."""
    py = python_check or _check_python()
    checklist = [
        _score_python(py),
        _score_packs_dir(root),
        _score_claude_projects(home=home),
        _score_cursor_projects(home=home),
        _score_lint(root),
        _score_golden_count(root),
    ]
    score = sum(c.points or 0 for c in checklist)
    return score, checklist


def cmd_doctor(
    root: Path | None = None,
    *,
    home: Path | None = None,
    score: bool = False,
) -> DoctorReport:
    report = DoctorReport()
    report.checks.append(_check_python())
    report.checks.append(_check_pyyaml())
    report.checks.append(_check_claude_projects(home=home))
    report.checks.append(_check_cursor_projects(home=home))
    report.checks.extend(_check_layout(root))
    if score:
        report.score, report.checklist = compute_score(
            root,
            home=home,
            python_check=report.checks[0],
        )
    return report
