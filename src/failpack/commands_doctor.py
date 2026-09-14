"""failpack doctor — environment and workspace health checks."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from failpack.commands_capture import claude_projects_dir
from failpack.commands_list import list_packs
from failpack.paths import FAILPACK_DIR, PACKS_DIR, failpack_dir, find_root


MIN_PYTHON = (3, 11)


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    detail: str
    fix: str | None = None


@dataclass
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks) and bool(self.checks)

    def summary_lines(self) -> list[str]:
        lines = ["failpack doctor"]
        for c in self.checks:
            mark = "OK" if c.ok else "FAIL"
            lines.append(f"  [{mark}] {c.name}: {c.detail}")
            if c.fix:
                label = "fix" if not c.ok else "tip"
                lines.append(f"         {label}: {c.fix}")
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
        fix=f"Install Python {need}+ and reinstall failpack "
        f"(pip install 'failpack @ git+https://github.com/JiangSkirk/failpack.git').",
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
    When sessions are found, tip ``capture --claude-latest``.
    """
    projects = claude_projects_dir(home=home)
    if not projects.is_dir():
        return DoctorCheck(
            "claude-projects",
            True,
            f"not found ({projects}) — optional",
            fix=(
                "Install/use Claude Code, or capture a fixture / exported JSONL. "
                "Try: failpack demo"
            ),
        )

    sessions = [p for p in projects.rglob("*.jsonl") if p.is_file()]
    n = len(sessions)
    if n == 0:
        return DoctorCheck(
            "claude-projects",
            True,
            f"found at {projects} (0 session *.jsonl)",
            fix="After a Claude Code run, try: failpack capture --claude-latest --id my-failure",
        )

    newest = max(sessions, key=lambda p: p.stat().st_mtime)
    return DoctorCheck(
        "claude-projects",
        True,
        f"found at {projects} ({n} session{'s' if n != 1 else ''})",
        fix=(
            f"Newest: {newest.name} — try: "
            "failpack capture --claude-latest --id my-failure"
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
                    "failpack capture --claude-latest --id my-failure   "
                    "# or: failpack demo"
                ),
            )
        )
    else:
        checks.append(DoctorCheck("packs", True, detail))
    return checks


def cmd_doctor(root: Path | None = None, *, home: Path | None = None) -> DoctorReport:
    report = DoctorReport()
    report.checks.append(_check_python())
    report.checks.append(_check_pyyaml())
    report.checks.append(_check_claude_projects(home=home))
    report.checks.extend(_check_layout(root))
    return report
