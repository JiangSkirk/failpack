"""failpack demo — one-command ~60-second wow path."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from failpack import __version__
from failpack.commands_capture import cmd_capture
from failpack.commands_doctor import cmd_doctor
from failpack.commands_init import cmd_init
from failpack.commands_migrate import cmd_migrate
from failpack.commands_promote import cmd_promote
from failpack.commands_replay import cmd_replay
from failpack.commands_status import cmd_status
from failpack.paths import find_root, packs_dir

DEMO_PACK_ID = "demo-five-minute"
DEMO_FIXTURE_RESOURCE = "demo-failure.jsonl"


@dataclass
class DemoReport:
    pack_id: str
    pack_dir: Path
    lines: list[str] = field(default_factory=list)
    ok: bool = True
    fast: bool = False

    def summary_lines(self) -> list[str]:
        return list(self.lines)


def demo_fixture_bytes() -> bytes:
    """Load the shipped demo transcript (repo fixtures or package data)."""
    here = Path(__file__).resolve()
    repo_fixture = here.parents[2] / "fixtures" / "claude-code-failure.jsonl"
    if repo_fixture.is_file():
        return repo_fixture.read_bytes()
    ref = resources.files("failpack").joinpath("data", DEMO_FIXTURE_RESOURCE)
    return ref.read_bytes()


def _emit(report: DemoReport, msg: str) -> None:
    report.lines.append(msg)


def _run_fast_demo(
    report: DemoReport,
    *,
    project: Path,
    pack_id: str,
    keep: bool,
) -> DemoReport:
    """Compact stranger path: capture → promote → replay (no doctor/break/migrate)."""
    with tempfile.TemporaryDirectory(prefix="failpack-demo-") as tmp:
        fixture = Path(tmp) / "demo-failure.jsonl"
        fixture.write_bytes(demo_fixture_bytes())

        _emit(report, f"failpack demo --fast  (~60s wow)  ·  failpack {__version__}")
        _emit(report, "")
        _emit(report, f"==> 1/3  capture bundled fixture → '{pack_id}'")
        pack = cmd_capture(fixture, pack_id=pack_id, root=project, force=True)
        _emit(report, f"Captured pack '{pack.name}' → {pack}")

        _emit(report, "")
        _emit(report, "==> 2/3  promote → golden")
        cmd_promote(pack_id, root=project)
        _emit(report, f"Promoted pack '{pack_id}' to golden")

        _emit(report, "")
        _emit(report, "==> 3/3  replay — should PASS")
        replay_ok = cmd_replay(pack_id, root=project)
        # Compact: RESULT line only (full check dump stays available via replay)
        result_lines = [ln for ln in replay_ok.summary_lines() if ln.startswith("RESULT:")]
        if result_lines:
            report.lines.extend(result_lines)
        else:
            report.lines.extend(replay_ok.summary_lines())
        if not replay_ok.ok:
            report.ok = False
            _emit(report, "RESULT: FAIL (expected PASS on clean replay)")
            return report

        _emit(report, "")
        if keep:
            _emit(report, f"Done (~60s). Demo pack left at {pack} (status=golden).")
            _emit(report, f"Clean up with:  failpack rm {pack_id} --force")
        else:
            shutil.rmtree(pack)
            report.pack_dir = pack
            _emit(report, "Done (~60s). Demo pack removed (--no-keep).")

        _emit(
            report,
            "Next: failpack capture --claude-latest --id my-failure  "
            "·  failpack demo   # full path with break/restore",
        )
        _emit(report, "RESULT: OK")
        return report


def cmd_demo(
    *,
    root: Path | None = None,
    pack_id: str = DEMO_PACK_ID,
    keep: bool = True,
    skip_break: bool = False,
    fast: bool = False,
) -> DemoReport:
    """Run the built-in capture → promote → replay (+ intentional break) path.

    ``fast=True`` compresses the stranger wow path to ~60 seconds: capture →
    promote → replay only (skips doctor dump, status dump, break/restore,
    migrate). Mirrors README::

        pip install "git+https://github.com/JiangSkirk/failpack.git" && failpack demo --fast
    """
    project = find_root(root) if root is None else root.resolve()
    if not packs_dir(project).is_dir():
        cmd_init(project)

    report = DemoReport(pack_id=pack_id, pack_dir=packs_dir(project) / pack_id, fast=fast)

    if fast:
        return _run_fast_demo(report, project=project, pack_id=pack_id, keep=keep)

    with tempfile.TemporaryDirectory(prefix="failpack-demo-") as tmp:
        fixture = Path(tmp) / "demo-failure.jsonl"
        fixture.write_bytes(demo_fixture_bytes())

        _emit(report, f"==> 1/8  failpack --version (expect {__version__})")
        _emit(report, f"failpack {__version__}")

        _emit(report, "")
        _emit(report, "==> 2/8  doctor — env + .failpack/ layout")
        doctor = cmd_doctor(project)
        report.lines.extend(doctor.summary_lines())
        if not doctor.ok:
            report.ok = False
            _emit(report, "RESULT: FAIL (doctor)")
            return report

        _emit(report, "")
        _emit(report, f"==> 3/8  capture bundled fixture → pack '{pack_id}'")
        pack = cmd_capture(fixture, pack_id=pack_id, root=project, force=True)
        _emit(report, f"Captured pack '{pack.name}' → {pack}")

        _emit(report, "")
        _emit(report, "==> 4/8  promote → golden assertions.yaml")
        cmd_promote(pack_id, root=project)
        status = cmd_status(pack_id, root=project)
        report.lines.extend(status.summary_lines())

        _emit(report, "")
        _emit(report, "==> 5/8  replay — should PASS")
        replay_ok = cmd_replay(pack_id, root=project)
        report.lines.extend(replay_ok.summary_lines())
        if not replay_ok.ok:
            report.ok = False
            _emit(report, "RESULT: FAIL (expected PASS on clean replay)")
            return report

        error_txt = pack / "artifacts" / "error.txt"
        backup = pack / "artifacts" / "error.txt.bak"

        if not skip_break:
            _emit(report, "")
            _emit(
                report,
                "==> 6/8  intentional break — mutate artifact, replay should FAIL",
            )
            shutil.copy2(error_txt, backup)
            with error_txt.open("a", encoding="utf-8") as fh:
                fh.write("\nMUTATED_BY_DEMO\n")

            replay_fail = cmd_replay(pack_id, root=project)
            report.lines.extend(replay_fail.summary_lines())
            if replay_fail.ok:
                shutil.move(str(backup), error_txt)
                report.ok = False
                _emit(report, "RESULT: FAIL (expected FAIL after intentional break)")
                return report
            _emit(
                report,
                "(exit 1 — expected FAIL; check expected/actual/hint/diff above)",
            )

            _emit(report, "")
            _emit(report, "==> 7/8  restore artifact → replay should PASS again")
            shutil.move(str(backup), error_txt)
            replay_restored = cmd_replay(pack_id, root=project)
            report.lines.extend(replay_restored.summary_lines())
            if not replay_restored.ok:
                report.ok = False
                _emit(report, "RESULT: FAIL (expected PASS after restore)")
                return report
        else:
            _emit(report, "")
            _emit(report, "==> 6–7/8  skipped intentional break (--skip-break)")

        _emit(report, "")
        _emit(report, "==> 8/8  migrate (should no-op — already current)")
        mig = cmd_migrate(root=project)
        report.lines.extend(mig.summary_lines())

        _emit(report, "")
        if keep:
            _emit(report, f"Done. Demo pack left at {pack} (status=golden).")
            _emit(report, f"Clean up with:  failpack rm {pack_id} --force")
        else:
            shutil.rmtree(pack)
            report.pack_dir = pack
            _emit(report, "Done. Demo pack removed (--no-keep).")

        _emit(
            report,
            "Tip: failpack demo --fast  for the ~60s stranger path; "
            "failpack capture --claude-latest --id my-failure  for a real session.",
        )
        _emit(report, "RESULT: OK")
        return report
