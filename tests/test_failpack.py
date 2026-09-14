"""End-to-end tests for FailPack capture → promote → replay + list/status."""

from __future__ import annotations

import io
import json
import shutil
import time
from pathlib import Path

import pytest
import yaml

from failpack import __version__
from failpack.cli import build_parser, main
from failpack.color import paint, use_color
from failpack.commands_capture import cmd_capture, find_newest_jsonl, resolve_transcript_path
from failpack.commands_doctor import cmd_doctor
from failpack.commands_init import cmd_init
from failpack.commands_list import cmd_list
from failpack.commands_promote import cmd_promote
from failpack.commands_replay import cmd_replay, cmd_replay_all
from failpack.commands_status import cmd_status
from failpack.pack import glob_fingerprint, read_meta, sha256_file

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "fixtures" / "claude-code-failure.jsonl"
FIXTURE_WRONG_CMD = REPO / "fixtures" / "claude-code-wrong-test-cmd.jsonl"
FIXTURE_PERM = REPO / "fixtures" / "claude-code-permission-denied.jsonl"
DEMO_ID = "demo-missing-import"
DEMO_WRONG_CMD = "demo-wrong-test-cmd"
DEMO_PERM = "demo-permission-denied"
GOLDEN_IDS = (DEMO_ID, DEMO_WRONG_CMD, DEMO_PERM)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    cmd_init(tmp_path)
    return tmp_path


def _capture_and_promote(workspace: Path, fixture: Path = FIXTURE, pack_id: str = DEMO_ID) -> str:
    pack = cmd_capture(fixture, pack_id=pack_id, root=workspace)
    cmd_promote(pack_id, root=workspace)
    return pack.name


def test_replay_passes_on_golden(workspace: Path) -> None:
    _capture_and_promote(workspace)
    report = cmd_replay(DEMO_ID, root=workspace)
    assert report.ok, "\n".join(report.summary_lines())


def test_replay_fails_when_assertion_mutated(workspace: Path) -> None:
    _capture_and_promote(workspace)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    assert data["substrings"], "expected at least one substring assertion"
    data["substrings"][0]["contains"] = "THIS_STRING_DOES_NOT_EXIST_IN_ARTIFACTS"
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert not report.ok
    failed = [c for c in report.checks if not c.ok and c.name.startswith("substring:")]
    assert failed
    assert failed[0].expected and "contains" in failed[0].expected
    assert failed[0].actual == "not found"
    assert failed[0].hint and "re-promote" in failed[0].hint
    summary = "\n".join(report.summary_lines(color=False))
    assert "expected:" in summary
    assert "actual:" in summary
    assert "hint:" in summary
    assert "re-promote after intentional change" in summary


def test_replay_fails_when_artifact_mutated(workspace: Path) -> None:
    _capture_and_promote(workspace)
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    error_path = pack / "artifacts" / "error.txt"
    original = error_path.read_text(encoding="utf-8")
    error_path.write_text(original + "\nMUTATED_BY_TEST\n", encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert not report.ok
    failed = [c for c in report.checks if not c.ok and "fingerprint:artifacts/error.txt" in c.name]
    assert failed
    assert failed[0].expected and failed[0].actual
    assert failed[0].expected != failed[0].actual
    assert failed[0].hint and "artifact drifted" in failed[0].hint
    assert "artifacts/error.txt" in failed[0].hint
    summary = "\n".join(report.summary_lines(color=False))
    assert "artifact drifted — inspect artifacts/error.txt" in summary


def test_replay_fails_when_exit_code_assertion_breaks(workspace: Path) -> None:
    _capture_and_promote(workspace)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data["exit_code"] = 0
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert not report.ok
    assert any(c.name == "exit_code" and not c.ok for c in report.checks)


def test_replay_fails_when_min_events_breaks(workspace: Path) -> None:
    _capture_and_promote(workspace)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data["min_events"] = 9999
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert not report.ok
    assert any(c.name == "min_events" and not c.ok for c in report.checks)


def test_replay_fails_when_glob_fingerprint_breaks(workspace: Path) -> None:
    _capture_and_promote(workspace)
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    written = pack / "artifacts" / "files" / "app" / "main.py"
    written.write_text(written.read_text(encoding="utf-8") + "\n# mutated\n", encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert not report.ok
    assert any(not c.ok and c.name.startswith("glob_fingerprint:") for c in report.checks)


def test_promote_writes_min_events_and_glob_fingerprint(workspace: Path) -> None:
    _capture_and_promote(workspace)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    assert data["min_events"] == 11
    assert data["glob_fingerprint"]["pattern"] == "artifacts/files/**"
    assert data["glob_fingerprint"]["file_count"] == 2
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    digest, matched = glob_fingerprint(pack, "artifacts/files/**")
    assert digest == data["glob_fingerprint"]["sha256"]
    assert len(matched) == 2


def test_backward_compatible_without_optional_assertions(workspace: Path) -> None:
    """Packs that omit min_events / glob_fingerprint still replay."""
    _capture_and_promote(workspace)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data.pop("min_events", None)
    data.pop("glob_fingerprint", None)
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert report.ok, "\n".join(report.summary_lines())
    assert not any(c.name == "min_events" for c in report.checks)
    assert not any(c.name.startswith("glob_fingerprint:") for c in report.checks)


@pytest.mark.parametrize("pack_id", GOLDEN_IDS)
def test_shipped_golden_pack_replays_clean(pack_id: str) -> None:
    demo = REPO / ".failpack" / "packs" / pack_id
    assert demo.is_dir(), f"golden pack missing: {pack_id}"
    report = cmd_replay(pack_id, root=REPO)
    assert report.ok, "\n".join(report.summary_lines())


def test_list_and_status_for_shipped_packs() -> None:
    rows = cmd_list(REPO)
    ids = {r.id for r in rows}
    assert DEMO_ID in ids
    assert DEMO_WRONG_CMD in ids
    assert DEMO_PERM in ids
    by_id = {r.id: r for r in rows}
    assert by_id[DEMO_ID].status == "golden"
    assert by_id[DEMO_ID].exit_code == 1
    assert by_id[DEMO_ID].promoted_at
    assert by_id[DEMO_WRONG_CMD].exit_code == 4
    assert by_id[DEMO_PERM].exit_code == 13

    status = cmd_status(DEMO_ID, root=REPO)
    lines = "\n".join(status.summary_lines())
    assert "status:       golden" in lines
    assert "min_events" in lines
    assert "glob_fingerprint" in lines


def test_list_status_in_workspace(workspace: Path) -> None:
    assert cmd_list(workspace) == []
    _capture_and_promote(workspace)
    rows = cmd_list(workspace)
    assert len(rows) == 1
    assert rows[0].id == DEMO_ID
    assert rows[0].status == "golden"

    before_promote = cmd_capture(FIXTURE_WRONG_CMD, pack_id="captured-only", root=workspace)
    assert before_promote.name == "captured-only"
    rows = cmd_list(workspace)
    statuses = {r.id: r.status for r in rows}
    assert statuses["captured-only"] == "captured"
    assert statuses[DEMO_ID] == "golden"

    st = cmd_status("captured-only", root=workspace)
    assert st.assertions is None
    assert any("none" in line.lower() for line in st.summary_lines())


def test_fingerprint_helper_changes_with_content(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    a.write_text("one", encoding="utf-8")
    h1 = sha256_file(a)
    a.write_text("two", encoding="utf-8")
    h2 = sha256_file(a)
    assert h1 != h2


def test_capture_force_overwrites(workspace: Path) -> None:
    cmd_capture(FIXTURE, pack_id="tmp-pack", root=workspace)
    first = (workspace / ".failpack" / "packs" / "tmp-pack" / "meta.json").read_text()
    cmd_capture(FIXTURE, pack_id="tmp-pack", root=workspace, force=True)
    second = (workspace / ".failpack" / "packs" / "tmp-pack" / "meta.json").read_text()
    assert "tmp-pack" in second
    assert first
    shutil.rmtree(workspace / ".failpack" / "packs" / "tmp-pack")


def test_capture_from_claude_project(workspace: Path, tmp_path: Path) -> None:
    project = tmp_path / "claude-projects" / "encoded-cwd"
    project.mkdir(parents=True)
    older = project / "old.jsonl"
    newer = project / "new.jsonl"
    older.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    newer.write_text(FIXTURE_WRONG_CMD.read_text(encoding="utf-8"), encoding="utf-8")
    # ensure mtime ordering
    older.touch()
    time.sleep(0.05)
    newer.write_text(FIXTURE_WRONG_CMD.read_text(encoding="utf-8"), encoding="utf-8")

    found = find_newest_jsonl(tmp_path / "claude-projects")
    assert found.name == "new.jsonl"

    pack = cmd_capture(
        None,
        pack_id="from-claude",
        root=workspace,
        from_claude_project=tmp_path / "claude-projects",
    )
    meta = read_meta(pack)
    assert meta["id"] == "from-claude"
    assert meta["exit_code"] == 4


def test_capture_directory_picks_newest_jsonl(workspace: Path, tmp_path: Path) -> None:
    """Passing a directory (not a .jsonl) auto-selects newest *.jsonl inside."""
    project = tmp_path / "sessions"
    project.mkdir()
    older = project / "old.jsonl"
    newer = project / "new.jsonl"
    older.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    time.sleep(0.05)
    newer.write_text(FIXTURE_WRONG_CMD.read_text(encoding="utf-8"), encoding="utf-8")

    resolved = resolve_transcript_path(project)
    assert resolved.name == "new.jsonl"

    pack = cmd_capture(project, pack_id="from-dir", root=workspace)
    assert read_meta(pack)["exit_code"] == 4


def test_capture_glob(workspace: Path) -> None:
    pack = cmd_capture(
        None,
        pack_id="from-glob",
        root=workspace,
        pattern=str(REPO / "fixtures" / "claude-code-wrong-test-cmd.jsonl"),
    )
    assert read_meta(pack)["exit_code"] == 4


def test_capture_path_glob_string(workspace: Path) -> None:
    # Quoted glob via Path that still contains glob chars
    pattern_path = Path(str(REPO / "fixtures" / "claude-code-*.jsonl"))
    resolved = resolve_transcript_path(pattern_path)
    assert resolved.is_file()
    pack = cmd_capture(pattern_path, pack_id="glob-path", root=workspace)
    assert pack.is_dir()


def test_capture_stdin(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = FIXTURE.read_bytes()

    class _Stdin:
        buffer = io.BytesIO(data)

    monkeypatch.setattr("failpack.commands_capture.sys.stdin", _Stdin())
    pack = cmd_capture(None, pack_id="from-stdin", root=workspace, stdin=True)
    meta = read_meta(pack)
    assert meta["source_transcript"] == "<stdin>"
    assert meta["exit_code"] == 1


def test_wrong_cmd_fixture_promotes_without_glob_fingerprint(workspace: Path) -> None:
    _capture_and_promote(workspace, FIXTURE_WRONG_CMD, DEMO_WRONG_CMD)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_WRONG_CMD / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    assert data["exit_code"] == 4
    assert data["min_events"] == 8
    assert "glob_fingerprint" not in data  # no written files in this session
    report = cmd_replay(DEMO_WRONG_CMD, root=workspace)
    assert report.ok, "\n".join(report.summary_lines())


def test_doctor_ok_on_repo() -> None:
    report = cmd_doctor(REPO)
    assert report.ok, "\n".join(report.summary_lines())
    names = {c.name for c in report.checks}
    assert "python" in names
    assert "pyyaml" in names
    assert "layout" in names
    assert "packs" in names
    packs = next(c for c in report.checks if c.name == "packs")
    assert "3 pack" in packs.detail
    assert "golden" in packs.detail


def test_doctor_missing_layout(tmp_path: Path) -> None:
    report = cmd_doctor(tmp_path)
    assert not report.ok
    layout = next(c for c in report.checks if c.name == "layout")
    assert not layout.ok
    assert layout.fix and "failpack init" in layout.fix
    # python + pyyaml should still pass
    assert next(c for c in report.checks if c.name == "python").ok
    assert next(c for c in report.checks if c.name == "pyyaml").ok


def test_doctor_empty_workspace(workspace: Path) -> None:
    report = cmd_doctor(workspace)
    assert report.ok, "\n".join(report.summary_lines())
    packs = next(c for c in report.checks if c.name == "packs")
    assert packs.ok
    assert "0 packs" in packs.detail
    assert packs.fix and "capture" in packs.fix


def test_replay_all_shipped_goldens() -> None:
    report = cmd_replay_all(root=REPO)
    assert report.ok, "\n".join(report.summary_lines())
    ids = {r.pack_id for r in report.reports}
    assert DEMO_ID in ids
    assert DEMO_WRONG_CMD in ids
    assert DEMO_PERM in ids
    assert all(r.ok for r in report.reports)


def test_permission_denied_fixture_promotes(workspace: Path) -> None:
    _capture_and_promote(workspace, FIXTURE_PERM, DEMO_PERM)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_PERM / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    assert data["exit_code"] == 13
    assert data["min_events"] == 8
    assert any("Permission denied" in s["contains"] for s in data["substrings"])
    # Write attempt is recorded under artifacts/files even though the tool errored
    assert data["glob_fingerprint"]["file_count"] == 1
    report = cmd_replay(DEMO_PERM, root=workspace)
    assert report.ok, "\n".join(report.summary_lines())


def test_replay_json_roundtrip(workspace: Path) -> None:
    _capture_and_promote(workspace)
    report = cmd_replay(DEMO_ID, root=workspace)
    payload = json.loads(report.to_json())
    assert payload["pack_id"] == DEMO_ID
    assert payload["ok"] is True
    assert payload["checks"]
    assert all("name" in c and "ok" in c for c in payload["checks"])

    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data["exit_code"] = 0
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    bad = cmd_replay(DEMO_ID, root=workspace)
    bad_payload = json.loads(bad.to_json())
    assert bad_payload["ok"] is False
    exit_check = next(c for c in bad_payload["checks"] if c["name"] == "exit_code")
    assert exit_check["ok"] is False
    assert exit_check["expected"] == "0"
    assert exit_check["actual"] == "1"
    assert "re-promote" in exit_check["hint"]


def test_replay_all_json_includes_packs(workspace: Path) -> None:
    _capture_and_promote(workspace)
    report = cmd_replay_all(root=workspace)
    payload = json.loads(report.to_json())
    assert payload["ok"] is True
    assert payload["packs"][0]["pack_id"] == DEMO_ID


def test_version_is_0_3_0() -> None:
    assert __version__ == "0.3.0"
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0


def test_help_mentions_examples() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "examples:" in help_text
    assert "NO_COLOR" in help_text
    replay_help = None
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        for name, sub in action.choices.items():
            if name == "replay":
                replay_help = sub.format_help()
    assert replay_help is not None
    assert "--json" in replay_help
    assert "examples:" in replay_help


def test_no_color_disables_ansi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert use_color() is False
    assert paint("FAIL", "red") == "FAIL"


def test_force_color_enables_ansi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert use_color() is True
    assert "\033[" in paint("FAIL", "red")


def test_cli_replay_json_flag(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _capture_and_promote(workspace)
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "replay", DEMO_ID, "--json"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["pack_id"] == DEMO_ID


def test_replay_all_skips_non_golden_and_fails_on_broken(workspace: Path) -> None:
    _capture_and_promote(workspace)
    cmd_capture(FIXTURE_WRONG_CMD, pack_id="captured-only", root=workspace)

    ok_report = cmd_replay_all(root=workspace)
    assert ok_report.ok
    assert [r.pack_id for r in ok_report.reports] == [DEMO_ID]
    assert "captured-only" in ok_report.skipped_non_golden

    # break the golden pack
    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data["exit_code"] = 0
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    bad = cmd_replay_all(root=workspace)
    assert not bad.ok
    assert any(not r.ok for r in bad.reports)
    summary = "\n".join(bad.summary_lines())
    assert "RESULT: FAIL" in summary


def test_replay_all_empty_workspace(workspace: Path) -> None:
    report = cmd_replay_all(root=workspace)
    assert report.ok
    assert report.reports == []
    assert "no golden packs" in "\n".join(report.summary_lines()).lower()
