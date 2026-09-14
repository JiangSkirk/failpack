"""failpack replay — verify golden assertions against pack artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from failpack.pack import artifacts_dir, read_assertions, read_meta, sha256_file
from failpack.paths import require_pack


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
