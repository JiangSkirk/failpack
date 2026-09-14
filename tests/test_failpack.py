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
from failpack.commands_capture import (
    cmd_capture,
    find_claude_latest,
    find_cursor_latest,
    find_newest_jsonl,
    resolve_transcript_path,
)
from failpack.commands_doctor import cmd_doctor
from failpack.commands_init import cmd_init
from failpack.commands_list import cmd_list, format_table
from failpack.commands_migrate import cmd_migrate
from failpack.commands_promote import cmd_promote, cmd_re_promote, suggest_assertions
from failpack.commands_replay import cmd_replay, cmd_replay_all
from failpack.commands_show import cmd_show
from failpack.commands_status import cmd_status
from failpack.commands_watch import cmd_watch
from failpack.diffutil import short_unified_diff
from failpack.events import (
    bash_output_contains,
    denied_tool_names,
    tool_denied_contains,
)
from failpack.pack import glob_fingerprint, read_meta, sha256_file
from failpack.schema import CURRENT_SCHEMA_VERSION
from failpack.transcript import load_jsonl

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "fixtures" / "claude-code-failure.jsonl"
FIXTURE_WRONG_CMD = REPO / "fixtures" / "claude-code-wrong-test-cmd.jsonl"
FIXTURE_PERM = REPO / "fixtures" / "claude-code-permission-denied.jsonl"
FIXTURE_TOOL_DENIED = REPO / "fixtures" / "claude-code-tool-denied.jsonl"
DEMO_ID = "demo-missing-import"
DEMO_WRONG_CMD = "demo-wrong-test-cmd"
DEMO_PERM = "demo-permission-denied"
DEMO_TOOL_DENIED = "demo-tool-denied"
GOLDEN_IDS = (DEMO_ID, DEMO_WRONG_CMD, DEMO_PERM, DEMO_TOOL_DENIED)


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
    assert "STORY:" in summary
    assert "What broke:" in summary
    assert "Assertion:" in summary
    assert "Next:" in summary


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
    assert failed[0].diff and "MUTATED_BY_TEST" in failed[0].diff
    assert "--- expected/artifacts/error.txt" in failed[0].diff
    summary = "\n".join(report.summary_lines(color=False))
    assert "artifact drifted — inspect artifacts/error.txt" in summary
    assert "diff:" in summary
    assert "MUTATED_BY_TEST" in summary

    # --no-diff / show_diff=False suppresses the unified diff
    quiet = cmd_replay(DEMO_ID, root=workspace, show_diff=False)
    quiet_fail = next(c for c in quiet.checks if not c.ok and "fingerprint:artifacts/error.txt" in c.name)
    assert quiet_fail.diff is None
    quiet_summary = "\n".join(quiet.summary_lines(color=False))
    assert "diff:" not in quiet_summary


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
    assert DEMO_TOOL_DENIED in ids
    by_id = {r.id: r for r in rows}
    assert by_id[DEMO_ID].status == "golden"
    assert by_id[DEMO_ID].exit_code == 1
    assert by_id[DEMO_ID].promoted_at
    assert by_id[DEMO_WRONG_CMD].exit_code == 4
    assert by_id[DEMO_PERM].exit_code == 13
    assert by_id[DEMO_TOOL_DENIED].exit_code == 126

    status = cmd_status(DEMO_ID, root=REPO)
    lines = "\n".join(status.summary_lines())
    assert "status:       golden" in lines
    assert "schema:" in lines
    assert "min_events" in lines
    assert "glob_fingerprint" in lines

    show = cmd_show(DEMO_TOOL_DENIED, root=REPO)
    show_lines = "\n".join(show.summary_lines(color=False))
    assert "failpack show: demo-tool-denied" in show_lines
    assert "tool_denied_contains:Bash" in show_lines
    assert "bash_output_contains:" in show_lines
    assert "artifacts/error.txt" in show_lines
    assert show.meta.get("promoted_at")
    payload = json.loads(show.to_json())
    assert payload["pack_id"] == DEMO_TOOL_DENIED
    assert payload["exit_code"] == 126
    assert "artifacts/digest.json" in payload["artifacts"]


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
    assert "claude-projects" in names
    assert "cursor-projects" in names
    assert "layout" in names
    assert "packs" in names
    packs = next(c for c in report.checks if c.name == "packs")
    # Assert shipped fixture goldens by id — do not hardcode exact pack count.
    # `failpack demo --fast` may leave demo-five-minute as an extra golden.
    rows = cmd_list(REPO)
    by_id = {r.id: r for r in rows}
    for gid in GOLDEN_IDS:
        assert gid in by_id, f"shipped golden missing: {gid}"
        assert by_id[gid].status == "golden"
    golden_n = sum(1 for r in rows if r.status == "golden")
    assert golden_n >= len(GOLDEN_IDS)
    assert f"{len(rows)} pack" in packs.detail
    assert f"{golden_n} golden" in packs.detail


def test_doctor_score_on_repo() -> None:
    report = cmd_doctor(REPO, score=True)
    assert report.score is not None
    assert 0 <= report.score <= 100
    # Repo has python + packs_dir + lint + goldens → at least 90
    # (claude_projects / cursor_projects may be 0 without agent homes)
    assert report.score >= 90
    names = [c.name for c in report.checklist]
    assert names == [
        "python",
        "packs_dir",
        "claude_projects",
        "cursor_projects",
        "lint",
        "golden_count",
    ]
    by_name = {c.name: c for c in report.checklist}
    assert by_name["python"].ok and by_name["python"].points == 25
    assert by_name["packs_dir"].ok and by_name["packs_dir"].points == 25
    assert by_name["lint"].ok and by_name["lint"].points == 20
    assert by_name["golden_count"].ok and by_name["golden_count"].points == 20
    rows = cmd_list(REPO)
    golden_n = sum(1 for r in rows if r.status == "golden")
    assert golden_n >= len(GOLDEN_IDS)
    assert by_name["golden_count"].detail.startswith(f"{golden_n} golden")
    assert by_name["claude_projects"].max_points == 5
    assert by_name["cursor_projects"].max_points == 5
    text = "\n".join(report.summary_lines(with_score=True))
    assert "READINESS SCORE:" in text
    assert "checklist:" in text
    assert f"{report.score}/100" in text


def test_doctor_score_empty_workspace(workspace: Path, tmp_path: Path) -> None:
    empty_home = tmp_path / "no-agents"
    empty_home.mkdir()
    report = cmd_doctor(workspace, home=empty_home, score=True)
    assert report.score is not None
    by_name = {c.name: c for c in report.checklist}
    assert by_name["python"].points == 25
    assert by_name["packs_dir"].points == 25
    assert by_name["claude_projects"].points == 0
    assert by_name["cursor_projects"].points == 0
    assert by_name["lint"].ok  # no packs → PASS with 0 checked
    assert by_name["lint"].points == 20
    assert by_name["golden_count"].points == 0
    assert report.score == 70


def test_doctor_score_missing_layout(tmp_path: Path) -> None:
    empty_home = tmp_path / "home"
    empty_home.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    report = cmd_doctor(root, home=empty_home, score=True)
    assert not report.ok
    assert report.score is not None
    by_name = {c.name: c for c in report.checklist}
    assert by_name["packs_dir"].points == 0
    assert by_name["packs_dir"].fix and "demo --fast" in by_name["packs_dir"].fix
    assert by_name["lint"].points == 0
    assert by_name["golden_count"].points == 0
    assert by_name["python"].points == 25
    assert by_name["claude_projects"].points == 0
    assert by_name["cursor_projects"].points == 0
    assert report.score == 25
    text = "\n".join(report.summary_lines(with_score=True))
    assert "RESULT: NEEDS SETUP" in text
    assert "next:" in text
    assert "failpack demo --fast" in text


def test_cli_doctor_score_exit_zero(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "doctor", "--score"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "READINESS SCORE:" in out
    assert "checklist:" in out
    assert "golden_count" in out


def test_cli_doctor_strict_fails_without_layout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(root), "doctor", "--strict"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "RESULT: NEEDS SETUP" in out
    assert "failpack demo --fast" in out


def test_cli_doctor_needs_setup_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """NEEDS SETUP is machineable: exit 1 (not only stdout RESULT)."""
    root = tmp_path / "bare"
    root.mkdir()
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(root), "doctor"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "RESULT: NEEDS SETUP" in out
    assert "next:" in out
    assert "failpack demo --fast" in out


def test_cli_doctor_score_needs_setup_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(root), "doctor", "--score"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "RESULT: NEEDS SETUP" in out
    assert "READINESS SCORE:" in out


def test_doctor_empty_cwd_does_not_inherit_ancestor_failpack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stranger/accept friction: nested empty cwd must not score parent packs."""
    ancestor = tmp_path / "workspace"
    (ancestor / ".failpack" / "packs").mkdir(parents=True)
    # Plant a golden-looking layout so climb would falsely look "set up".
    golden = ancestor / ".failpack" / "packs" / "ancestor-golden"
    (golden / "artifacts").mkdir(parents=True)
    (golden / "meta.json").write_text(
        '{"id":"ancestor-golden","status":"golden","exit_code":1}\n',
        encoding="utf-8",
    )
    empty = ancestor / "foo" / "empty-doctor"
    empty.mkdir(parents=True)
    monkeypatch.chdir(empty)
    empty_home = tmp_path / "no-agents"
    empty_home.mkdir()
    report = cmd_doctor(None, home=empty_home, score=True)
    assert not report.ok
    text = "\n".join(report.summary_lines(with_score=True))
    assert "RESULT: NEEDS SETUP" in text
    assert report.score is not None
    assert report.score <= 25  # python only; no inherited packs_dir/goldens
    by_name = {c.name: c for c in report.checklist}
    assert by_name["packs_dir"].points == 0
    assert by_name["golden_count"].points == 0
    layout = next(c for c in report.checks if c.name == "layout")
    assert not layout.ok
    assert str(empty.resolve()) in layout.detail or "no .failpack" in layout.detail


def test_cli_doctor_empty_cwd_no_ancestor_exit_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ancestor = tmp_path / "workspace"
    (ancestor / ".failpack" / "packs").mkdir(parents=True)
    empty = ancestor / "foo" / "empty-doctor"
    empty.mkdir(parents=True)
    monkeypatch.chdir(empty)
    with pytest.raises(SystemExit) as exc:
        main(["doctor", "--score"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "RESULT: NEEDS SETUP" in out
    assert "READINESS SCORE:" in out


def test_demo_fast_nested_empty_cwd_creates_local_failpack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """1.5.11: demo must not write into an ancestor .failpack/ from nested cwd."""
    from failpack.commands_demo import cmd_demo

    ancestor = tmp_path / "workspace"
    (ancestor / ".failpack" / "packs").mkdir(parents=True)
    ancestor_pack = ancestor / ".failpack" / "packs" / "ancestor-only"
    ancestor_pack.mkdir()
    (ancestor_pack / "meta.json").write_text(
        '{"id":"ancestor-only","status":"golden","exit_code":1}\n',
        encoding="utf-8",
    )
    empty = ancestor / "accept" / "nested-empty"
    empty.mkdir(parents=True)
    monkeypatch.chdir(empty)

    report = cmd_demo(root=None, pack_id="demo-local", keep=True, fast=True)
    assert report.ok, "\n".join(report.summary_lines())

    local_pack = empty / ".failpack" / "packs" / "demo-local"
    assert local_pack.is_dir()
    assert (local_pack / "assertions.yaml").is_file()
    assert not (ancestor / ".failpack" / "packs" / "demo-local").exists()
    assert ancestor_pack.is_dir()  # ancestor packs unchanged

    empty_home = tmp_path / "no-agents"
    empty_home.mkdir()
    doctor = cmd_doctor(None, home=empty_home, score=True)
    assert doctor.ok, "\n".join(doctor.summary_lines(with_score=True))
    text = "\n".join(doctor.summary_lines(with_score=True))
    assert "RESULT: OK" in text
    assert doctor.score is not None and doctor.score >= 90


def test_cli_demo_fast_nested_cwd_then_doctor_ok(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI: nested empty accept cwd → demo --fast local + doctor OK."""
    ancestor = tmp_path / "workspace"
    (ancestor / ".failpack" / "packs").mkdir(parents=True)
    empty = ancestor / "accept" / "nested-cli"
    empty.mkdir(parents=True)
    monkeypatch.chdir(empty)

    with pytest.raises(SystemExit) as demo_exc:
        main(["demo", "--fast", "--id", "cli-nested-local"])
    assert demo_exc.value.code == 0
    out = capsys.readouterr().out
    assert "RESULT: OK" in out
    assert (empty / ".failpack" / "packs" / "cli-nested-local").is_dir()
    assert not (ancestor / ".failpack" / "packs" / "cli-nested-local").exists()

    with pytest.raises(SystemExit) as doctor_exc:
        main(["doctor", "--score"])
    assert doctor_exc.value.code == 0
    doctor_out = capsys.readouterr().out
    assert "RESULT: OK" in doctor_out
    assert "NEEDS SETUP" not in doctor_out


def test_capture_nested_empty_cwd_does_not_write_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First-time capture without local layout must not climb to ancestor."""
    ancestor = tmp_path / "workspace"
    (ancestor / ".failpack" / "packs").mkdir(parents=True)
    empty = ancestor / "accept" / "no-local"
    empty.mkdir(parents=True)
    monkeypatch.chdir(empty)

    with pytest.raises(FileNotFoundError, match=r"failpack|init|demo"):
        cmd_capture(FIXTURE, pack_id="should-not-climb", root=None)
    assert not (ancestor / ".failpack" / "packs" / "should-not-climb").exists()
    assert not (empty / ".failpack").exists()

    # init + capture → local packs; ancestor unchanged
    cmd_init(None)
    pack = cmd_capture(FIXTURE, pack_id="local-cap", root=None)
    assert pack == empty / ".failpack" / "packs" / "local-cap"
    assert pack.is_dir()
    assert not (ancestor / ".failpack" / "packs" / "local-cap").exists()


def test_doctor_missing_layout(tmp_path: Path) -> None:
    report = cmd_doctor(tmp_path)
    assert not report.ok
    layout = next(c for c in report.checks if c.name == "layout")
    assert not layout.ok
    assert layout.fix and "failpack demo --fast" in layout.fix
    assert "failpack init" in (layout.fix or "")
    text = "\n".join(report.summary_lines())
    assert "RESULT: NEEDS SETUP" in text
    assert "next:" in text
    # python + pyyaml should still pass
    assert next(c for c in report.checks if c.name == "python").ok
    assert next(c for c in report.checks if c.name == "pyyaml").ok
    assert next(c for c in report.checks if c.name == "claude-projects").ok


def test_doctor_empty_workspace(workspace: Path) -> None:
    report = cmd_doctor(workspace)
    assert report.ok, "\n".join(report.summary_lines())
    packs = next(c for c in report.checks if c.name == "packs")
    assert packs.ok
    assert "0 packs" in packs.detail
    assert packs.fix and ("capture" in packs.fix or "demo" in packs.fix)


def test_replay_all_shipped_goldens() -> None:
    report = cmd_replay_all(root=REPO)
    assert report.ok, "\n".join(report.summary_lines())
    ids = {r.pack_id for r in report.reports}
    assert DEMO_ID in ids
    assert DEMO_WRONG_CMD in ids
    assert DEMO_PERM in ids
    assert DEMO_TOOL_DENIED in ids
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


def test_version_is_1_3_0() -> None:
    assert __version__ == "1.5.11"
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
    assert "--no-diff" in replay_help
    assert "examples:" in replay_help


def test_short_unified_diff_truncates() -> None:
    expected = "line\n" * 5
    actual = "line\n" * 4 + "changed\n"
    diff = short_unified_diff(expected, actual, max_lines=8)
    assert "--- expected" in diff
    assert "+++ actual" in diff
    assert "changed" in diff


def test_promote_writes_schema_and_expected(workspace: Path) -> None:
    _capture_and_promote(workspace)
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    meta = read_meta(pack)
    assert meta["schema_version"] == CURRENT_SCHEMA_VERSION
    assert (pack / "expected" / "artifacts" / "error.txt").is_file()
    # Snapshot matches golden artifact at promote time
    assert (pack / "expected" / "artifacts" / "error.txt").read_text(
        encoding="utf-8"
    ) == (pack / "artifacts" / "error.txt").read_text(encoding="utf-8")


def test_migrate_noop_when_current(workspace: Path) -> None:
    _capture_and_promote(workspace)
    first = cmd_migrate(root=workspace)
    assert first.ok
    assert "already at schema version" in first.message
    assert DEMO_ID in first.already_current
    assert not first.migrated
    lines = "\n".join(first.summary_lines())
    assert "nothing to do" in lines

    # Strip schema_version → migrate upgrades
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    meta = read_meta(pack)
    meta.pop("schema_version", None)
    (pack / "meta.json").write_text(
        __import__("json").dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    second = cmd_migrate(root=workspace)
    assert DEMO_ID in second.migrated
    assert read_meta(pack)["schema_version"] == CURRENT_SCHEMA_VERSION


def test_migrate_empty_workspace(workspace: Path) -> None:
    report = cmd_migrate(root=workspace)
    assert report.ok
    assert "no packs" in report.message.lower() or "current" in report.message.lower()


def test_watch_capture_promote_replay(workspace: Path) -> None:
    pid, report = cmd_watch(FIXTURE, pack_id="watched", root=workspace, force=True)
    assert pid == "watched"
    assert report.ok, "\n".join(report.summary_lines())
    meta = read_meta(workspace / ".failpack" / "packs" / "watched")
    assert meta["status"] == "golden"
    assert meta["schema_version"] == CURRENT_SCHEMA_VERSION


def test_cli_watch_exits_1_on_fail(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # First watch succeeds
    with pytest.raises(SystemExit) as ok:
        main(["--root", str(workspace), "watch", str(FIXTURE), "--id", "w1", "--force"])
    assert ok.value.code == 0
    out_ok = capsys.readouterr().out
    assert "PASS" in out_ok

    # Mutate artifact then replay via watch overwrite? Instead break after promote:
    pack = workspace / ".failpack" / "packs" / "w1"
    err = pack / "artifacts" / "error.txt"
    err.write_text(err.read_text(encoding="utf-8") + "\nBROKEN\n", encoding="utf-8")
    with pytest.raises(SystemExit) as bad:
        main(["--root", str(workspace), "replay", "w1"])
    assert bad.value.code == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "diff:" in out


def test_cli_watch_prints_story_and_next_on_fail(
    workspace: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Watch FAIL must surface the same STORY / next: tips as replay."""
    from failpack import commands_watch as watch_mod
    from failpack.commands_promote import cmd_promote

    def promote_then_break(pack_id: str, **kwargs):  # type: ignore[no-untyped-def]
        result = cmd_promote(pack_id, **kwargs)
        pack = workspace / ".failpack" / "packs" / pack_id
        err = pack / "artifacts" / "error.txt"
        if err.is_file():
            err.write_text(err.read_text(encoding="utf-8") + "\nWATCH-BROKEN\n", encoding="utf-8")
        return result

    monkeypatch.setattr(watch_mod, "cmd_promote", promote_then_break)
    with pytest.raises(SystemExit) as bad:
        main(["--root", str(workspace), "watch", str(FIXTURE), "--id", "watch-fail", "--force"])
    assert bad.value.code == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "STORY:" in out
    assert "next: failpack explain watch-fail" in out
    assert "failpack diff watch-fail" in out
    assert "re-promote watch-fail" in out


def test_cli_replay_no_diff_flag(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _capture_and_promote(workspace)
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    err = pack / "artifacts" / "error.txt"
    err.write_text(err.read_text(encoding="utf-8") + "\nX\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "replay", DEMO_ID, "--no-diff"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "diff:" not in out


def test_diff_expected_vs_actual(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from failpack.commands_diff import cmd_diff

    _capture_and_promote(workspace, pack_id="diff-me")
    ok = cmd_diff("diff-me", root=workspace)
    assert ok.ok
    assert ok.matched >= 1
    assert all(f.status == "match" for f in ok.files)

    err = workspace / ".failpack" / "packs" / "diff-me" / "artifacts" / "error.txt"
    err.write_text(err.read_text(encoding="utf-8") + "\nDIFF-MUTATION\n", encoding="utf-8")
    bad = cmd_diff("diff-me", root=workspace)
    assert not bad.ok
    assert bad.differed >= 1
    summary = "\n".join(bad.summary_lines(color=False))
    assert "RESULT: FAIL" in summary
    assert "differ" in summary
    assert "DIFF-MUTATION" in summary
    assert "next: failpack explain diff-me" in summary

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "diff", "diff-me", "--json"])
    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["pack_id"] == "diff-me"
    assert any(f["status"] == "differ" for f in payload["files"])

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "diff", "diff-me", "--no-diff"])
    assert exc.value.code == 1
    quiet = capsys.readouterr().out
    assert "differ" in quiet
    assert "DIFF-MUTATION" not in quiet


def test_list_and_packs_json(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _capture_and_promote(workspace, pack_id="json-pack")
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "list", "--json"])
    assert exc.value.code == 0
    rows = json.loads(capsys.readouterr().out)
    assert isinstance(rows, list)
    assert any(r["id"] == "json-pack" and r["status"] == "golden" for r in rows)
    assert "exit_code" in rows[0]
    assert "promoted_at" in rows[0]

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "packs", "--json"])
    assert exc.value.code == 0
    alias = json.loads(capsys.readouterr().out)
    assert alias == rows


def test_cli_list_empty_prints_next_tip(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cmd_init(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(tmp_path), "list"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "No packs found" in out
    assert "demo --fast" in out
    assert "capture --claude-latest" in out

    with pytest.raises(SystemExit) as empty_json:
        main(["--root", str(tmp_path), "list", "--json"])
    assert empty_json.value.code == 0
    assert json.loads(capsys.readouterr().out) == []


def test_init_ci_writes_workflow(tmp_path: Path) -> None:
    fp, workflow = cmd_init(tmp_path, ci=True)
    assert fp.is_dir()
    assert workflow is not None
    assert workflow.is_file()
    text = workflow.read_text(encoding="utf-8")
    assert "failpack-replay" in text
    assert "JiangSkirk/failpack" in text
    assert "@v1.5.0" in text
    tip = (fp / "README.md").read_text(encoding="utf-8")
    assert "failpack demo" in tip
    assert "--claude-latest" in tip
    assert "--cursor-latest" in tip
    assert "failpack show" in tip
    assert "failpack diff" in tip
    assert "promote --suggest" in tip
    assert "STORY" in tip or "next:" in tip
    # Idempotent: second init --ci does not clobber
    workflow.write_text("# custom\n", encoding="utf-8")
    _, again = cmd_init(tmp_path, ci=True)
    assert again.read_text(encoding="utf-8") == "# custom\n"


def test_shipped_packs_have_schema_version() -> None:
    for pack_id in GOLDEN_IDS:
        meta = read_meta(REPO / ".failpack" / "packs" / pack_id)
        assert meta.get("schema_version") == CURRENT_SCHEMA_VERSION
        expected = REPO / ".failpack" / "packs" / pack_id / "expected"
        assert expected.is_dir(), f"expected/ missing for {pack_id}"


def test_pre_commit_hook_example_exists() -> None:
    hook = REPO / "examples" / "pre-commit-hook.sh"
    assert hook.is_file()
    text = hook.read_text(encoding="utf-8")
    assert "failpack replay --all" in text


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
    summary = "\n".join(bad.summary_lines(color=False))
    assert "RESULT: FAIL" in summary
    assert "SUMMARY:" in summary
    assert "1 failed" in summary
    assert f"failed packs: {DEMO_ID}" in summary
    assert "re-promote" in summary
    assert "failpack explain" in summary
    assert "failpack diff" in summary
    assert f"next: failpack explain {DEMO_ID}" in summary
    assert "STORY:" in summary


def test_explain_fail_and_pass(workspace: Path) -> None:
    from failpack.commands_explain import cmd_explain

    _capture_and_promote(workspace, pack_id="explain-me")
    ok = cmd_explain("explain-me", root=workspace)
    assert ok.ok
    text = "\n".join(ok.summary_lines())
    assert "STORY:" in text
    assert "passed all" in text
    assert "RESULT: PASS" in text

    assertions_path = workspace / ".failpack" / "packs" / "explain-me" / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data["exit_code"] = 0
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    bad = cmd_explain("explain-me", root=workspace)
    assert not bad.ok
    story = "\n".join(bad.summary_lines())
    assert "What broke:" in story
    assert "exit code" in story.lower()
    assert "Assertion:  exit_code" in story
    assert "Next:" in story
    assert "re-promote explain-me" in story
    assert "RESULT: FAIL" in story
    assert "next: failpack diff explain-me" in story
    assert "promote --suggest explain-me" in story

    # omit id → explain every failing golden
    all_fail = cmd_explain(root=workspace)
    assert not all_fail.ok
    all_text = "\n".join(all_fail.summary_lines())
    assert "explain-me" in all_text
    assert "next: failpack diff" in all_text


def test_cli_explain(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _capture_and_promote(workspace, pack_id="cli-explain")
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "explain", "cli-explain"])
    assert exc.value.code == 0
    assert "STORY:" in capsys.readouterr().out


def test_replay_all_empty_workspace(workspace: Path) -> None:
    report = cmd_replay_all(root=workspace)
    assert report.ok
    assert report.reports == []
    assert "no golden packs" in "\n".join(report.summary_lines()).lower()


def _fake_claude_home(tmp_path: Path) -> Path:
    """Build a fake $HOME with ~/.claude/projects/<proj>/*.jsonl (never real ~/.claude)."""
    home = tmp_path / "fake-home"
    project = home / ".claude" / "projects" / "encoded-cwd"
    project.mkdir(parents=True)
    older = project / "old-session.jsonl"
    newer = project / "new-session.jsonl"
    older.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    time.sleep(0.05)
    newer.write_text(FIXTURE_WRONG_CMD.read_text(encoding="utf-8"), encoding="utf-8")
    return home


def test_find_claude_latest_uses_home_fixture(tmp_path: Path) -> None:
    home = _fake_claude_home(tmp_path)
    found = find_claude_latest(home=home)
    assert found.name == "new-session.jsonl"
    assert found.is_relative_to(home / ".claude" / "projects")



def test_capture_claude_latest_with_fake_home(workspace: Path, tmp_path: Path) -> None:
    home = _fake_claude_home(tmp_path)
    pack = cmd_capture(
        None,
        pack_id="claude-latest-pack",
        root=workspace,
        claude_latest=True,
        home=home,
    )
    meta = read_meta(pack)
    assert meta["id"] == "claude-latest-pack"
    assert meta["exit_code"] == 4
    assert meta["source_transcript"].startswith("<claude-latest:")


def test_claude_latest_hermetic_capture_promote_replay(
    workspace: Path, tmp_path: Path
) -> None:
    """Fake HOME + shipped fixture → capture --claude-latest → promote → replay.

    Proves the Claude one-shot wow path without a live Claude Code install
    and without inventing “user” packs.
    """
    home = tmp_path / "fake-home"
    project = home / ".claude" / "projects" / "hermetic-demo"
    project.mkdir(parents=True)
    (project / "session.jsonl").write_text(
        FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
    )

    pack = cmd_capture(
        None,
        pack_id="claude-hermetic",
        root=workspace,
        claude_latest=True,
        home=home,
    )
    meta = read_meta(pack)
    assert meta["id"] == "claude-hermetic"
    assert meta["exit_code"] == 1
    assert meta["source_transcript"].startswith("<claude-latest:")
    assert "session.jsonl" in meta["source_transcript"]

    cmd_promote("claude-hermetic", root=workspace)
    report = cmd_replay("claude-hermetic", root=workspace)
    assert report.ok, "\n".join(report.summary_lines())


def test_cli_claude_latest_hermetic_e2e(
    workspace: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI path: HOME=fake + fixture → capture --claude-latest → promote → replay."""
    home = tmp_path / "fake-home"
    project = home / ".claude" / "projects" / "hermetic-demo"
    project.mkdir(parents=True)
    (project / "session.jsonl").write_text(
        FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(home))

    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--root",
                str(workspace),
                "capture",
                "--claude-latest",
                "--id",
                "via-hermetic",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Claude one-shot" in out
    assert "via-hermetic" in out

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "promote", "--suggest", "--write", "via-hermetic"])
    assert exc.value.code == 0

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "replay", "via-hermetic"])
    assert exc.value.code == 0
    replay_out = capsys.readouterr().out
    assert "RESULT: PASS" in replay_out


def test_cli_capture_claude_latest_honors_HOME(
    workspace: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _fake_claude_home(tmp_path)
    monkeypatch.setenv("HOME", str(home))
    # Path.home() reads HOME on Unix
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--root",
                str(workspace),
                "capture",
                "--claude-latest",
                "--id",
                "via-cli",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "via-cli" in out
    assert "Claude one-shot" in out
    assert "using:" in out
    assert "Next: failpack promote --suggest --write via-cli" in out
    assert "applies" in out or "--suggest alone" in out
    meta = read_meta(workspace / ".failpack" / "packs" / "via-cli")
    assert meta["exit_code"] == 4


def test_claude_latest_missing_projects_dir(tmp_path: Path) -> None:
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir()
    with pytest.raises(
        FileNotFoundError,
        match=r"claude-hermetic|demo --fast|one-shot|\.claude/projects",
    ):
        find_claude_latest(home=empty_home)


def test_claude_latest_conflicts_with_path(workspace: Path, tmp_path: Path) -> None:
    home = _fake_claude_home(tmp_path)
    with pytest.raises(ValueError, match="only one"):
        resolve_transcript_path(FIXTURE, claude_latest=True, home=home)


def test_capture_same_id_tips_force_or_new_id(workspace: Path) -> None:
    cmd_capture(FIXTURE, pack_id="dup-id", root=workspace)
    with pytest.raises(FileExistsError, match=r"--force|new id") as exc:
        cmd_capture(FIXTURE, pack_id="dup-id", root=workspace)
    msg = str(exc.value)
    assert "--force" in msg
    assert "dup-id-2" in msg or "new id" in msg.lower() or "--id" in msg


def test_re_promote_refreshes_assertions_after_intentional_fix(workspace: Path) -> None:
    _capture_and_promote(workspace)
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    error_path = pack / "artifacts" / "error.txt"
    original = error_path.read_text(encoding="utf-8")
    error_path.write_text(original + "\nINTENTIONAL_NEW_SIGNAL\n", encoding="utf-8")

    broken = cmd_replay(DEMO_ID, root=workspace)
    assert not broken.ok

    # Intentionally accept the new golden: re-promote from current artifacts
    cmd_re_promote(DEMO_ID, root=workspace)
    assertions = yaml.safe_load((pack / "assertions.yaml").read_text(encoding="utf-8"))
    # Fingerprint for error.txt should match the mutated file
    from failpack.pack import sha256_file as _sha

    err_fp = next(f for f in assertions["fingerprints"] if f["path"] == "artifacts/error.txt")
    assert err_fp["sha256"] == _sha(error_path)
    assert (pack / "expected" / "artifacts" / "error.txt").read_text(
        encoding="utf-8"
    ) == error_path.read_text(encoding="utf-8")

    ok = cmd_replay(DEMO_ID, root=workspace)
    assert ok.ok, "\n".join(ok.summary_lines())


def test_cli_re_promote(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _capture_and_promote(workspace)
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "re-promote", DEMO_ID])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Re-promoted" in out
    assert DEMO_ID in out


def test_list_format_table_is_aligned() -> None:
    rows = cmd_list(REPO)
    table = format_table(rows)
    assert table
    assert table[0].startswith("ID")
    assert "STATUS" in table[0]
    assert all("\t" not in line for line in table)  # space-aligned, not TSV
    body = "\n".join(table)
    assert DEMO_ID in body
    assert "golden" in body


def test_cli_list_prints_table(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(REPO), "list"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "ID" in out
    assert "STATUS" in out
    assert DEMO_ID in out
    # No progress spinner / percent noise
    assert "%" not in out
    assert "…" not in out


def test_help_mentions_claude_latest_and_re_promote() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "--claude-latest" in help_text or "claude-latest" in help_text
    assert "cursor-latest" in help_text
    assert "re-promote" in help_text
    assert "suggest" in help_text
    cap_help = None
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        for name, sub in action.choices.items():
            if name == "capture":
                cap_help = sub.format_help()
    assert cap_help is not None
    assert "--claude-latest" in cap_help
    assert "--cursor-latest" in cap_help


def test_examples_docs_exist() -> None:
    demo = REPO / "examples" / "five-minute-demo.sh"
    assert demo.is_file()
    text = demo.read_text(encoding="utf-8")
    assert "failpack demo" in text
    assert "--fast" in text
    assert "~60s" in text or "60s" in text
    claude_doc = REPO / "examples" / "claude-latest-demo.md"
    assert claude_doc.is_file()
    body = claude_doc.read_text(encoding="utf-8")
    assert "--claude-latest" in body
    assert "re-promote" in body
    assert "Claude one-shot" in body or "one-shot" in body
    assert "promote --suggest" in body
    assert "fake HOME" in body or "fake-home" in body
    assert "claude-latest-hermetic" in body
    assert "demo --claude-hermetic" in body
    hermetic = REPO / "examples" / "claude-latest-hermetic.sh"
    assert hermetic.is_file()
    hermetic_text = hermetic.read_text(encoding="utf-8")
    assert "demo --claude-hermetic" in hermetic_text
    assert "delegating" in hermetic_text or "thin" in hermetic_text.lower() or "wrapper" in hermetic_text.lower() or "failpack demo --claude-hermetic" in hermetic_text
    cursor_doc = REPO / "examples" / "cursor-latest-demo.md"
    assert cursor_doc.is_file()
    cursor_body = cursor_doc.read_text(encoding="utf-8")
    assert "--cursor-latest" in cursor_body
    assert "fake HOME" in cursor_body or "fake $HOME" in cursor_body or "fake-home" in cursor_body
    assert "demo --cursor-hermetic" in cursor_body
    assert "cursor-latest-hermetic" in cursor_body
    cursor_hermetic = REPO / "examples" / "cursor-latest-hermetic.sh"
    assert cursor_hermetic.is_file()
    cursor_hermetic_text = cursor_hermetic.read_text(encoding="utf-8")
    assert "demo --cursor-hermetic" in cursor_hermetic_text
    assert (
        "delegating" in cursor_hermetic_text
        or "thin" in cursor_hermetic_text.lower()
        or "wrapper" in cursor_hermetic_text.lower()
        or "failpack demo --cursor-hermetic" in cursor_hermetic_text
    )
    walk = REPO / "examples" / "STRANGER_WALKTHROUGH.md"
    assert walk.is_file()
    walk_body = walk.read_text(encoding="utf-8")
    assert "git+https://github.com/JiangSkirk/failpack.git" in walk_body
    assert "pip install failpack" in walk_body
    assert "doctor --score" in walk_body
    assert "failpack demo --fast" in walk_body
    assert "~60s" in walk_body or "60s" in walk_body
    assert "demo-five-minute" in walk_body
    assert "promote --suggest" in walk_body
    assert "Claude one-shot" in walk_body or "claude-latest" in walk_body
    assert "claude-latest-hermetic" in walk_body
    assert "demo --claude-hermetic" in walk_body
    assert "cursor-latest-hermetic" in walk_body
    assert "demo --cursor-hermetic" in walk_body
    assert "cursor-projects" in walk_body
    assert "~/.local/bin" in walk_body
    assert "RELEASE_NOTES_1.5.11" in walk_body or "v1.5.11" in walk_body
    assert "RELEASE_NOTES_1.5.10" in walk_body or "v1.5.10" in walk_body
    assert "RELEASE_NOTES_1.5.9" in walk_body or "v1.5.9" in walk_body
    assert "RELEASE_NOTES_1.5.8" in walk_body or "v1.5.8" in walk_body
    assert "RELEASE_NOTES_1.5.7" in walk_body or "v1.5.7" in walk_body
    assert "RELEASE_NOTES_1.5.6" in walk_body or "v1.5.6" in walk_body
    assert "RELEASE_NOTES_1.5.5" in walk_body or "v1.5.5" in walk_body
    assert "RELEASE_NOTES_1.5.4" in walk_body or "v1.5.4" in walk_body
    assert "RELEASE_NOTES_1.5.3" in walk_body or "v1.5.3" in walk_body
    assert "RELEASE_NOTES_1.5.2" in walk_body or "v1.5.2" in walk_body
    assert "RELEASE_NOTES_1.5.0" in walk_body or "v1.5.0" in walk_body
    assert "failpack diff" in walk_body or "list --json" in walk_body or "packs --json" in walk_body
    assert "Clean up with:" in walk_body
    assert "failpack rm" in walk_body and "--force" in walk_body
    assert "rm -rf" not in walk_body
    assert "SUPPORT.md" in walk_body
    assert "1.5.11" in walk_body
    contributing = (REPO / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "1.5.11" in contributing
    assert "claude-latest-hermetic" in contributing
    assert "cursor-latest-hermetic" in contributing or "demo --cursor-hermetic" in contributing
    assert "8725598a@gmail.com" in contributing
    assert "SUPPORT.md" in contributing


def test_changelog_and_contributing_exist() -> None:
    assert (REPO / "CHANGELOG.md").is_file()
    assert (REPO / "CONTRIBUTING.md").is_file()
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "1.5.11" in changelog
    assert "1.5.10" in changelog
    assert "local_root" in changelog or "cwd-local" in changelog.lower() or "ancestor" in changelog.lower()
    assert "1.5.9" in changelog
    assert "1.5.8" in changelog
    assert "1.5.7" in changelog
    assert "cursor-hermetic" in changelog or "Hermetic Cursor" in changelog or "demo --cursor-hermetic" in changelog
    assert "NEEDS SETUP" in changelog
    assert "ancestor" in changelog.lower() or "doctor_root" in changelog or "cwd" in changelog.lower()
    assert "1.5.6" in changelog
    assert "claude-latest-hermetic" in changelog or "Hermetic Claude" in changelog
    assert "pages.yml" in changelog or "GitHub Pages" in changelog
    assert "1.5.4" in changelog
    assert "1.5.3" in changelog
    assert "1.5.2" in changelog
    assert "1.5.1" in changelog
    assert "1.5.0" in changelog
    assert "failpack rm" in changelog
    assert "NEEDS SETUP" in changelog
    assert "SUPPORT.md" in changelog
    assert "1.4.0" in changelog
    assert "1.3.0" in changelog
    assert "PyPI" in changelog or "pip install failpack" in changelog
    assert "1.2.0" in changelog
    assert "1.1.0" in changelog
    assert "1.0.0" in changelog
    assert "doctor --score" in changelog
    assert "cursor_projects" in changelog
    assert "next:" in changelog
    assert "Daily loop" in changelog or "watch" in changelog.lower()
    assert "PUBLISH.md" in changelog
    assert "QUALITY_BAR.md" in changelog
    assert "--fast" in changelog
    assert "failpack diff" in changelog
    assert "list --json" in changelog or "packs --json" in changelog
    assert "@v1.5.0" in changelog
    assert "@v1.4.0" in changelog
    assert "60s" in changelog or "~60" in changelog
    assert "one-shot" in changelog.lower() or "claude-latest" in changelog
    assert "--suggest" in changelog
    assert "--cursor-latest" in changelog
    assert "0.9.0" in changelog
    assert "0.7.0" in changelog
    assert "0.6.0" in changelog
    assert "0.5.0" in changelog
    assert "0.4.0" in changelog
    assert "tool_denied_contains" in changelog
    assert "failpack show" in changelog


def test_doctor_claude_projects_missing_home(tmp_path: Path, workspace: Path) -> None:
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir()
    report = cmd_doctor(workspace, home=empty_home)
    assert report.ok, "\n".join(report.summary_lines())
    claude = next(c for c in report.checks if c.name == "claude-projects")
    assert claude.ok
    assert "not found" in claude.detail
    assert claude.fix and "demo --fast" in claude.fix
    assert "--claude-latest" in (claude.fix or "")
    assert "claude-hermetic" in (claude.fix or "") or "fake HOME" in (claude.fix or "")
    cursor = next(c for c in report.checks if c.name == "cursor-projects")
    assert cursor.ok
    assert "not found" in cursor.detail
    assert cursor.fix and "demo" in cursor.fix
    assert "cursor-hermetic" in (cursor.fix or "") or "demo --fast" in (cursor.fix or "")
    assert "--cursor-latest" in (cursor.fix or "")


def test_doctor_claude_projects_with_sessions(tmp_path: Path, workspace: Path) -> None:
    home = _fake_claude_home(tmp_path)
    report = cmd_doctor(workspace, home=home)
    assert report.ok, "\n".join(report.summary_lines())
    claude = next(c for c in report.checks if c.name == "claude-projects")
    assert claude.ok
    assert "session" in claude.detail
    assert claude.fix and "--claude-latest" in claude.fix
    assert "One-shot" in (claude.fix or "") or "one-shot" in (claude.fix or "").lower()


def test_doctor_cursor_projects_with_sessions(tmp_path: Path, workspace: Path) -> None:
    home = _fake_cursor_home(tmp_path)
    _capture_and_promote(workspace, pack_id="cursor-score-pack")
    report = cmd_doctor(workspace, home=home, score=True)
    assert report.ok, "\n".join(report.summary_lines())
    cursor = next(c for c in report.checks if c.name == "cursor-projects")
    assert cursor.ok
    assert "transcript" in cursor.detail
    assert cursor.fix and "--cursor-latest" in cursor.fix
    by_name = {c.name: c for c in report.checklist}
    assert by_name["cursor_projects"].points == 5
    assert by_name["claude_projects"].points == 0
    # Soft Cursor points only — CI without Claude still healthy
    assert report.score is not None
    assert report.score == 95


def test_export_import_roundtrip(workspace: Path, tmp_path: Path) -> None:
    from failpack.commands_export import cmd_export
    from failpack.commands_import import cmd_import

    _capture_and_promote(workspace, pack_id="share-me")
    archive = tmp_path / "share-me.tgz"
    out = cmd_export("share-me", output=archive, root=workspace)
    assert out.is_file()
    assert out.stat().st_size > 0

    # Import into a fresh workspace
    other = tmp_path / "other"
    cmd_init(other)
    dest = cmd_import(archive, root=other)
    assert dest.name == "share-me"
    report = cmd_replay("share-me", root=other)
    assert report.ok, "\n".join(report.summary_lines())


def test_export_zip_and_import_rename(workspace: Path, tmp_path: Path) -> None:
    from failpack.commands_export import cmd_export
    from failpack.commands_import import cmd_import

    _capture_and_promote(workspace, pack_id="zip-me")
    archive = tmp_path / "zip-me.zip"
    cmd_export("zip-me", output=archive, root=workspace)
    dest = cmd_import(archive, root=workspace, rename="zip-me-copy")
    assert dest.name == "zip-me-copy"
    meta = read_meta(dest)
    assert meta["id"] == "zip-me-copy"
    assert cmd_replay("zip-me-copy", root=workspace).ok


def test_import_collision_requires_force_or_rename(workspace: Path, tmp_path: Path) -> None:
    from failpack.commands_export import cmd_export
    from failpack.commands_import import cmd_import

    _capture_and_promote(workspace, pack_id="collide")
    archive = tmp_path / "collide.tgz"
    cmd_export("collide", output=archive, root=workspace)
    with pytest.raises(FileExistsError, match="--force"):
        cmd_import(archive, root=workspace)
    dest = cmd_import(archive, root=workspace, force=True)
    assert dest.name == "collide"


def test_export_requires_golden(workspace: Path, tmp_path: Path) -> None:
    from failpack.commands_export import cmd_export

    cmd_capture(FIXTURE, pack_id="not-golden", root=workspace)
    with pytest.raises((ValueError, FileNotFoundError), match="[Pp]romote"):
        cmd_export("not-golden", output=tmp_path / "x.tgz", root=workspace)


def test_demo_end_to_end(workspace: Path) -> None:
    from failpack.commands_demo import cmd_demo

    report = cmd_demo(root=workspace, pack_id="demo-test", keep=True)
    assert report.ok, "\n".join(report.summary_lines())
    text = "\n".join(report.summary_lines())
    assert "failpack rm demo-test --force" in text
    assert "rm -rf" not in text
    assert (workspace / ".failpack" / "packs" / "demo-test" / "assertions.yaml").is_file()
    assert cmd_replay("demo-test", root=workspace).ok


def test_demo_fast_compact_path(workspace: Path) -> None:
    from failpack.commands_demo import cmd_demo

    report = cmd_demo(root=workspace, pack_id="demo-fast", keep=True, fast=True)
    assert report.ok, "\n".join(report.summary_lines())
    assert report.fast
    text = "\n".join(report.summary_lines())
    assert "~60s" in text
    assert "1/3" in text
    assert "2/8" not in text  # full doctor path skipped
    assert "RESULT: OK" in text
    assert "Clean up with:" in text
    assert "failpack rm demo-fast --force" in text
    assert "rm -rf" not in text
    assert (workspace / ".failpack" / "packs" / "demo-fast" / "assertions.yaml").is_file()


def test_cli_demo_fast(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "demo", "--fast", "--id", "cli-fast", "--no-keep"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "demo --fast" in out
    assert "~60s" in out
    assert "RESULT: OK" in out


def test_demo_claude_hermetic_library(workspace: Path) -> None:
    """Library path: demo --claude-hermetic without a live Claude install."""
    from failpack.commands_demo import (
        CLAUDE_HERMETIC_PACK_ID,
        claude_hermetic_fixture_bytes,
        cmd_demo,
    )

    assert claude_hermetic_fixture_bytes()  # bundled / repo fixture loads
    report = cmd_demo(root=workspace, claude_hermetic=True, keep=True)
    assert report.ok, "\n".join(report.summary_lines())
    assert report.claude_hermetic
    text = "\n".join(report.summary_lines())
    assert "demo --claude-hermetic" in text
    assert "PASS: hermetic Claude one-shot" in text
    assert "RESULT: OK" in text
    assert f"failpack rm {CLAUDE_HERMETIC_PACK_ID} --force" in text
    assert "rm -rf" not in text
    pack = workspace / ".failpack" / "packs" / CLAUDE_HERMETIC_PACK_ID
    assert (pack / "assertions.yaml").is_file()
    assert cmd_replay(CLAUDE_HERMETIC_PACK_ID, root=workspace).ok


def test_cli_demo_claude_hermetic(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI: failpack demo --claude-hermetic (and --fast) without Claude binary."""
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--root",
                str(workspace),
                "demo",
                "--claude-hermetic",
                "--fast",
                "--id",
                "cli-claude-hermetic",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "demo --claude-hermetic" in out
    assert "capture --claude-latest" in out or "claude-latest" in out
    assert "PASS: hermetic Claude one-shot" in out
    assert "RESULT: OK" in out
    assert "RESULT: PASS" in out
    assert (workspace / ".failpack" / "packs" / "cli-claude-hermetic" / "assertions.yaml").is_file()


def test_demo_claude_hermetic_tolerates_demo_leftover(workspace: Path) -> None:
    """Hermetic demo stays green when demo --fast leftover is already present."""
    from failpack.commands_demo import cmd_demo

    leftover = cmd_demo(root=workspace, pack_id="demo-five-minute", keep=True, fast=True)
    assert leftover.ok, "\n".join(leftover.summary_lines())
    report = cmd_demo(
        root=workspace, pack_id="claude-hermetic-with-leftover", claude_hermetic=True, keep=True
    )
    assert report.ok, "\n".join(report.summary_lines())
    assert (workspace / ".failpack" / "packs" / "demo-five-minute").is_dir()
    assert (workspace / ".failpack" / "packs" / "claude-hermetic-with-leftover").is_dir()


def test_demo_cursor_hermetic_library(workspace: Path) -> None:
    """Library path: demo --cursor-hermetic without a live Cursor install."""
    from failpack.commands_demo import (
        CURSOR_HERMETIC_PACK_ID,
        cmd_demo,
        cursor_hermetic_fixture_bytes,
    )

    assert cursor_hermetic_fixture_bytes()  # bundled / repo fixture loads
    report = cmd_demo(root=workspace, cursor_hermetic=True, keep=True)
    assert report.ok, "\n".join(report.summary_lines())
    assert report.cursor_hermetic
    text = "\n".join(report.summary_lines())
    assert "demo --cursor-hermetic" in text
    assert "PASS: hermetic Cursor one-shot" in text
    assert "RESULT: OK" in text
    assert f"failpack rm {CURSOR_HERMETIC_PACK_ID} --force" in text
    assert "rm -rf" not in text
    pack = workspace / ".failpack" / "packs" / CURSOR_HERMETIC_PACK_ID
    assert (pack / "assertions.yaml").is_file()
    assert cmd_replay(CURSOR_HERMETIC_PACK_ID, root=workspace).ok


def test_cli_demo_cursor_hermetic(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI: failpack demo --cursor-hermetic (and --fast) without Cursor binary."""
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--root",
                str(workspace),
                "demo",
                "--cursor-hermetic",
                "--fast",
                "--id",
                "cli-cursor-hermetic",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "demo --cursor-hermetic" in out
    assert "capture --cursor-latest" in out or "cursor-latest" in out
    assert "PASS: hermetic Cursor one-shot" in out
    assert "RESULT: OK" in out
    assert "RESULT: PASS" in out
    assert (workspace / ".failpack" / "packs" / "cli-cursor-hermetic" / "assertions.yaml").is_file()


def test_demo_cursor_hermetic_tolerates_demo_leftover(workspace: Path) -> None:
    """Cursor hermetic stays green when demo --fast leftover is already present."""
    from failpack.commands_demo import cmd_demo

    leftover = cmd_demo(root=workspace, pack_id="demo-five-minute", keep=True, fast=True)
    assert leftover.ok, "\n".join(leftover.summary_lines())
    report = cmd_demo(
        root=workspace, pack_id="cursor-hermetic-with-leftover", cursor_hermetic=True, keep=True
    )
    assert report.ok, "\n".join(report.summary_lines())
    assert (workspace / ".failpack" / "packs" / "demo-five-minute").is_dir()
    assert (workspace / ".failpack" / "packs" / "cursor-hermetic-with-leftover").is_dir()


def test_demo_hermetic_modes_are_mutually_exclusive(workspace: Path) -> None:
    from failpack.commands_demo import cmd_demo

    with pytest.raises(ValueError, match="only one"):
        cmd_demo(root=workspace, claude_hermetic=True, cursor_hermetic=True)


def test_demo_no_keep(workspace: Path) -> None:
    from failpack.commands_demo import cmd_demo

    report = cmd_demo(root=workspace, pack_id="demo-temp", keep=False, skip_break=True)
    assert report.ok, "\n".join(report.summary_lines())
    assert not (workspace / ".failpack" / "packs" / "demo-temp").exists()


def test_cli_export_import_demo(
    workspace: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _capture_and_promote(workspace, pack_id="cli-share")
    archive = tmp_path / "cli-share.tgz"
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "export", "cli-share", "-o", str(archive)])
    assert exc.value.code == 0
    assert archive.is_file()

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "import", str(archive), "--rename", "cli-share-2"])
    assert exc.value.code == 0

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "demo", "--id", "cli-demo", "--skip-break", "--no-keep"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "RESULT: OK" in out


def test_help_mentions_demo_export_import() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "demo" in help_text
    assert "export" in help_text
    assert "import" in help_text
    assert "show" in help_text
    assert "explain" in help_text
    assert "demo --claude-hermetic" in help_text
    assert "demo --cursor-hermetic" in help_text
    names = set()
    demo_help = None
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        names.update(action.choices.keys())
        for name, sub in action.choices.items():
            if name == "demo":
                demo_help = sub.format_help()
    assert "demo" in names
    assert "export" in names
    assert "import" in names
    assert "show" in names
    assert "explain" in names
    assert demo_help is not None
    assert "--claude-hermetic" in demo_help
    assert "--cursor-hermetic" in demo_help
    assert "--fast" in demo_help


def test_bundled_demo_fixture_loads() -> None:
    from failpack.commands_demo import (
        claude_hermetic_fixture_bytes,
        cursor_hermetic_fixture_bytes,
        demo_fixture_bytes,
    )

    data = demo_fixture_bytes()
    assert b"session_start" in data
    assert len(data) > 100
    hermetic = claude_hermetic_fixture_bytes()
    assert b"session_start" in hermetic
    assert hermetic == data  # same failure transcript content
    cursor = cursor_hermetic_fixture_bytes()
    assert b"session_start" in cursor
    assert cursor == data  # same Claude-compatible failure content


def test_readme_has_three_command_happy_path() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    assert "failpack capture --claude-latest" in text
    assert "failpack promote" in text
    assert "failpack replay" in text
    assert "failpack demo" in text
    assert "failpack show" in text
    assert "failpack explain" in text
    assert "1.5.11" in text
    assert "claude-latest-hermetic" in text
    assert "demo --claude-hermetic" in text
    assert "demo --cursor-hermetic" in text
    assert "cursor-latest-hermetic" in text
    assert "1.5.10" in text or "1.5.9" in text or "1.5.8" in text or "1.5.6" in text or "1.5.5" in text or "1.5.4" in text or "1.5.3" in text or "1.5.2" in text or "1.5.1" in text or "1.5.0" in text
    assert "1.5.0" in text
    assert "1.4.0" in text
    assert "1.3.0" in text
    assert "doctor --score" in text
    assert 'git+https://github.com/JiangSkirk/failpack.git' in text
    assert "pip install failpack" in text
    assert "when published" not in text.lower()
    assert "preferred once published" not in text.lower()
    assert "~60-second path" in text or "demo --fast" in text
    assert "Daily loop" in text
    assert "Pack lifecycle" in text
    assert "failpack report" in text
    assert "failpack lint" in text
    assert "failpack diff" in text
    assert "list --json" in text or "packs --json" in text
    assert "run-lint" in text
    assert "step-summary" in text
    assert "tool_denied_contains" in text
    assert "bash_output_contains" in text
    assert "--suggest" in text
    assert "--cursor-latest" in text
    assert "cursor_projects" in text
    assert "Claude one-shot" in text or "one-shot" in text.lower()
    assert "STRANGER_WALKTHROUGH" in text
    assert "badge.svg" in text
    assert "@v1.5.0" in text
    assert "regression memory" in text.lower()
    assert "Stet" in text
    assert "AgentClash" in text
    assert "stunning" not in text.lower()
    assert "8725598a@gmail.com" in text
    assert "SUPPORT.md" in text
    assert "jiangskirk.github.io/failpack" in text
    assert (REPO / "src" / "failpack" / "data" / "claude-code-failure.jsonl").is_file()
    assert (REPO / "src" / "failpack" / "data" / "cursor-agent-failure.jsonl").is_file()
    assert (REPO / "src" / "failpack" / "data" / "demo-failure.jsonl").is_file()
    assert (REPO / "fixtures" / "cursor-agent-failure.jsonl").is_file()
    assert (REPO / "docs" / "PACKS.md").is_file()
    assert (REPO / "docs" / "PUBLISH.md").is_file()
    assert (REPO / "docs" / "QUALITY_BAR.md").is_file()
    assert (REPO / "docs" / "SUPPORT.md").is_file()
    support = (REPO / "docs" / "SUPPORT.md").read_text(encoding="utf-8")
    assert "8725598a@gmail.com" in support
    assert "JiangSkirk" in support
    assert "issues" in support.lower()
    assert "Discord" in support  # stated as not offered
    quality = (REPO / "docs" / "QUALITY_BAR.md").read_text(encoding="utf-8")
    assert "PyPI" in quality
    assert "real-user" in quality.lower() or "real user" in quality.lower()
    assert "SUPPORT.md" in quality or "Support path" in quality
    assert "Done" in quality or "✅" in quality
    assert "1.5.11" in quality
    assert "Hermetic Claude" in quality or "hermetic" in quality.lower()
    assert "claude-latest-hermetic" in quality
    assert "demo --claude-hermetic" in quality
    assert "Hermetic Cursor" in quality or "cursor-hermetic" in quality
    assert "demo --cursor-hermetic" in quality
    assert "Still blocked" not in quality
    assert "first upload" in quality.lower() or "1.5.5" in quality
    assert "jiangskirk.github.io/failpack" in quality
    assert "pages.yml" in quality or "GitHub Pages" in quality or "workflow shipped" in quality.lower()
    assert "one-time" in quality.lower() or "Settings" in quality
    assert "do **not** claim" in quality.lower() or "do not claim" in quality.lower() or "404" in quality
    assert "demo-five-minute" in quality or "leave" in quality.lower()
    publish = (REPO / "docs" / "PUBLISH.md").read_text(encoding="utf-8")
    assert "python -m build" in publish
    assert "twine" in publish
    assert "testpypi" in publish.lower() or "TestPyPI" in publish
    assert "live on PyPI" in publish or "1.5.5" in publish
    assert "pip install failpack" in publish
    packs = (REPO / "docs" / "PACKS.md").read_text(encoding="utf-8")
    assert "demo-missing-import" in packs
    assert "demo --fast" in packs
    landing = (REPO / "docs" / "LANDING.md").read_text(encoding="utf-8")
    assert "failpack demo --fast" in landing
    assert "demo --claude-hermetic" in landing
    assert "demo --cursor-hermetic" in landing
    assert "pip install failpack" in landing
    assert "when published" not in landing.lower()
    site = (REPO / "site" / "index.html").read_text(encoding="utf-8")
    assert "failpack demo --fast" in site
    assert "demo --claude-hermetic" in site
    assert "demo --cursor-hermetic" in site
    assert "pip install failpack" in site
    assert 'git+https://github.com/JiangSkirk/failpack.git' in site
    assert "when published" not in site.lower()
    assert "1.5.11" in site
    assert "Checkout (placeholder)" in site or "checkout" in site.lower()
    assert "coming soon" in site.lower()
    assert "privacy.html" in site
    assert "terms.html" in site
    assert "8725598a@gmail.com" in site
    assert "pip install failpack" in text
    assert 'git+https://github.com/JiangSkirk/failpack.git' in text
    assert (REPO / ".github" / "workflows" / "pages.yml").is_file()
    pages_wf = (REPO / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "upload-pages-artifact" in pages_wf
    assert "deploy-pages" in pages_wf
    assert "github-pages" in pages_wf
    assert (REPO / "RELEASE_NOTES_1.5.11.md").is_file()
    notes1511 = (REPO / "RELEASE_NOTES_1.5.11.md").read_text(encoding="utf-8")
    assert "1.5.11" in notes1511
    assert "@v1.5.0" in notes1511
    assert "local_root" in notes1511 or "cwd" in notes1511.lower()
    assert "ancestor" in notes1511.lower()
    assert "demo --fast" in notes1511
    assert "jiangskirk.github.io/failpack" in notes1511
    assert "pip install failpack" in notes1511
    assert "when published" not in notes1511.lower()
    assert "do **not** claim" in notes1511.lower() or "do not claim" in notes1511.lower() or "404" in notes1511
    assert "PyPI" in notes1511
    assert "Do not re-upload" in notes1511 or "No PyPI" in notes1511 or "no PyPI" in notes1511.lower()
    assert (REPO / "RELEASE_NOTES_1.5.10.md").is_file()
    notes1510 = (REPO / "RELEASE_NOTES_1.5.10.md").read_text(encoding="utf-8")
    assert "1.5.10" in notes1510
    assert "@v1.5.0" in notes1510
    assert "NEEDS SETUP" in notes1510
    assert "ancestor" in notes1510.lower() or "cwd" in notes1510.lower()
    assert "jiangskirk.github.io/failpack" in notes1510
    assert "demo --fast" in notes1510
    assert "pip install failpack" in notes1510
    assert "when published" not in notes1510.lower()
    assert "do **not** claim" in notes1510.lower() or "do not claim" in notes1510.lower() or "404" in notes1510
    assert "PyPI" in notes1510
    assert "Do not re-upload" in notes1510 or "No PyPI" in notes1510 or "no PyPI" in notes1510.lower()
    assert (REPO / "RELEASE_NOTES_1.5.9.md").is_file()
    notes159 = (REPO / "RELEASE_NOTES_1.5.9.md").read_text(encoding="utf-8")
    assert "1.5.9" in notes159
    assert "@v1.5.0" in notes159
    assert "demo --cursor-hermetic" in notes159
    assert "cursor-hermetic" in notes159 or "Hermetic" in notes159
    assert "jiangskirk.github.io/failpack" in notes159
    assert "demo --fast" in notes159
    assert "pip install failpack" in notes159
    assert "when published" not in notes159.lower()
    assert "do **not** claim" in notes159.lower() or "do not claim" in notes159.lower() or "404" in notes159
    assert "PyPI" in notes159
    assert "Do not re-upload" in notes159 or "No PyPI" in notes159 or "no PyPI" in notes159.lower()
    assert (REPO / "RELEASE_NOTES_1.5.8.md").is_file()
    notes158 = (REPO / "RELEASE_NOTES_1.5.8.md").read_text(encoding="utf-8")
    assert "1.5.8" in notes158
    assert "@v1.5.0" in notes158
    assert "demo --claude-hermetic" in notes158
    assert "claude-hermetic" in notes158 or "Hermetic" in notes158
    assert "jiangskirk.github.io/failpack" in notes158
    assert "demo --fast" in notes158
    assert "pip install failpack" in notes158
    assert "when published" not in notes158.lower()
    assert "do **not** claim" in notes158.lower() or "do not claim" in notes158.lower() or "404" in notes158
    assert "PyPI" in notes158
    assert "Do not re-upload" in notes158 or "No PyPI" in notes158 or "no PyPI" in notes158.lower()
    assert (REPO / "RELEASE_NOTES_1.5.7.md").is_file()
    notes157 = (REPO / "RELEASE_NOTES_1.5.7.md").read_text(encoding="utf-8")
    assert "1.5.7" in notes157
    assert "@v1.5.0" in notes157
    assert "claude-latest-hermetic" in notes157 or "Hermetic" in notes157
    assert "jiangskirk.github.io/failpack" in notes157
    assert "demo --fast" in notes157
    assert "pip install failpack" in notes157
    assert "when published" not in notes157.lower()
    assert "do **not** claim" in notes157.lower() or "do not claim" in notes157.lower() or "404" in notes157
    assert "PyPI" in notes157
    assert (REPO / "RELEASE_NOTES_1.5.6.md").is_file()
    notes156 = (REPO / "RELEASE_NOTES_1.5.6.md").read_text(encoding="utf-8")
    assert "1.5.6" in notes156
    assert "@v1.5.0" in notes156
    assert "jiangskirk.github.io/failpack" in notes156
    assert "demo --fast" in notes156
    assert "pip install failpack" in notes156
    assert "when published" not in notes156.lower()
    assert "PyPI" in notes156
    assert (REPO / "RELEASE_NOTES_1.5.5.md").is_file()
    notes155 = (REPO / "RELEASE_NOTES_1.5.5.md").read_text(encoding="utf-8")
    assert "1.5.5" in notes155
    assert "@v1.5.0" in notes155
    assert "jiangskirk.github.io/failpack" in notes155
    assert "demo --fast" in notes155
    assert "pip install failpack" in notes155
    assert "placeholder" in notes155.lower()
    assert (REPO / "RELEASE_NOTES_1.5.4.md").is_file()
    notes154 = (REPO / "RELEASE_NOTES_1.5.4.md").read_text(encoding="utf-8")
    assert "1.5.4" in notes154
    assert "@v1.5.0" in notes154
    assert "failpack rm" in notes154
    assert "NEEDS SETUP" in notes154
    assert (REPO / "RELEASE_NOTES_1.5.3.md").is_file()
    notes153 = (REPO / "RELEASE_NOTES_1.5.3.md").read_text(encoding="utf-8")
    assert "1.5.3" in notes153
    assert "@v1.5.0" in notes153
    assert "demo-five-minute" in notes153 or "doctor" in notes153.lower()
    assert (REPO / "RELEASE_NOTES_1.5.2.md").is_file()
    notes152 = (REPO / "RELEASE_NOTES_1.5.2.md").read_text(encoding="utf-8")
    assert "1.5.2" in notes152
    assert "SUPPORT.md" in notes152
    assert "@v1.5.0" in notes152
    assert (REPO / "RELEASE_NOTES_1.5.0.md").is_file()
    notes15 = (REPO / "RELEASE_NOTES_1.5.0.md").read_text(encoding="utf-8")
    assert "1.5.0" in notes15
    assert "QUALITY_BAR" in notes15
    assert (REPO / "RELEASE_NOTES_1.4.0.md").is_file()
    notes14 = (REPO / "RELEASE_NOTES_1.4.0.md").read_text(encoding="utf-8")
    assert "1.4.0" in notes14
    assert "failpack diff" in notes14
    assert (REPO / "RELEASE_NOTES_1.3.0.md").is_file()
    notes13 = (REPO / "RELEASE_NOTES_1.3.0.md").read_text(encoding="utf-8")
    assert "1.3.0" in notes13
    assert "demo --fast" in notes13
    assert (REPO / "RELEASE_NOTES_1.2.0.md").is_file()
    notes12 = (REPO / "RELEASE_NOTES_1.2.0.md").read_text(encoding="utf-8")
    assert "1.2.0" in notes12
    assert "cursor_projects" in notes12 or "next:" in notes12
    assert (REPO / "RELEASE_NOTES_1.1.0.md").is_file()
    notes = (REPO / "RELEASE_NOTES_1.1.0.md").read_text(encoding="utf-8")
    assert "1.1.0" in notes
    assert "--suggest" in notes
    assert (REPO / "RELEASE_NOTES_1.0.0.md").is_file()
    assert "demo-tool-denied" in packs
    assert "demo-five-minute" in packs
    action_readme = (REPO / ".github" / "actions" / "failpack-replay" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "@v1.5.0" in action_readme
    assert "@main" in action_readme
    other_ci = (REPO / "examples" / "other-repo-ci.yml").read_text(encoding="utf-8")
    assert "@v1.5.0" in other_ci


def test_rm_refuses_golden_without_force(workspace: Path) -> None:
    from failpack.commands_rm import cmd_rm

    _capture_and_promote(workspace, pack_id="rm-golden")
    with pytest.raises(ValueError, match="golden"):
        cmd_rm("rm-golden", root=workspace)
    assert (workspace / ".failpack" / "packs" / "rm-golden").is_dir()

    cmd_rm("rm-golden", root=workspace, force=True)
    assert not (workspace / ".failpack" / "packs" / "rm-golden").exists()


def test_rm_deletes_captured_without_force(workspace: Path) -> None:
    from failpack.commands_rm import cmd_rm

    cmd_capture(FIXTURE, pack_id="rm-captured", root=workspace)
    cmd_rm("rm-captured", root=workspace)
    assert not (workspace / ".failpack" / "packs" / "rm-captured").exists()


def test_rename_updates_meta_and_assertions(workspace: Path) -> None:
    from failpack.commands_rename import cmd_rename
    from failpack.pack import read_assertions, read_meta

    _capture_and_promote(workspace, pack_id="old-name")
    dest = cmd_rename("old-name", "new-name", root=workspace)
    assert dest.name == "new-name"
    assert not (workspace / ".failpack" / "packs" / "old-name").exists()
    meta = read_meta(dest)
    assert meta["id"] == "new-name"
    assertions = read_assertions(dest)
    assert assertions["pack_id"] == "new-name"
    assert cmd_replay("new-name", root=workspace).ok


def test_rename_collision_and_invalid(workspace: Path) -> None:
    from failpack.commands_rename import cmd_rename

    _capture_and_promote(workspace, pack_id="keep-a")
    _capture_and_promote(workspace, pack_id="keep-b")
    with pytest.raises(FileExistsError):
        cmd_rename("keep-a", "keep-b", root=workspace)
    with pytest.raises(ValueError, match="Invalid pack id"):
        cmd_rename("keep-a", "../evil", root=workspace)
    with pytest.raises(ValueError, match="same"):
        cmd_rename("keep-a", "keep-a", root=workspace)


def test_promote_dry_run_does_not_write(workspace: Path) -> None:
    cmd_capture(FIXTURE, pack_id="dry-me", root=workspace)
    pack = workspace / ".failpack" / "packs" / "dry-me"
    result = cmd_promote("dry-me", root=workspace, dry_run=True)
    assert isinstance(result, dict)
    assert result["pack_id"] == "dry-me"
    assert "exit_code" in result
    assert "fingerprints" in result
    assert not (pack / "assertions.yaml").exists()
    assert read_meta(pack)["status"] == "captured"
    assert not (pack / "expected").exists()


def test_cli_promote_dry_run(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cmd_capture(FIXTURE, pack_id="cli-dry", root=workspace)
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "promote", "--dry-run", "cli-dry"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "pack_id: cli-dry" in out
    assert "exit_code:" in out
    assert not (workspace / ".failpack" / "packs" / "cli-dry" / "assertions.yaml").exists()

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "promote", "cli-dry", "--dry-run"])
    assert exc.value.code == 0


def test_assertion_schema_rejects_unknown_kind(workspace: Path) -> None:
    from failpack.assertions_schema import validate_assertions
    from failpack.pack import read_assertions

    _capture_and_promote(workspace, pack_id="schema-bad")
    pack = workspace / ".failpack" / "packs" / "schema-bad"
    path = pack / "assertions.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["regex_match"] = [{"path": "artifacts/error.txt", "pattern": ".*"}]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown assertion kind"):
        read_assertions(pack)
    with pytest.raises(ValueError, match="Unknown assertion kind"):
        validate_assertions(data)
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "replay", "schema-bad"])
    assert exc.value.code == 2


def test_assertion_schema_rejects_missing_fields() -> None:
    from failpack.assertions_schema import validate_assertions

    with pytest.raises(ValueError, match="missing required field"):
        validate_assertions(
            {
                "version": 1,
                "fingerprints": [{"path": "artifacts/error.txt"}],
            }
        )
    with pytest.raises(ValueError, match="missing required field"):
        validate_assertions(
            {
                "version": 1,
                "substrings": [{"path": "artifacts/error.txt"}],
            }
        )
    with pytest.raises(ValueError, match="missing required field"):
        validate_assertions(
            {
                "version": 1,
                "tool_denied_contains": [{}],
            }
        )


def test_completion_bash_and_zsh_smoke() -> None:
    from failpack.commands_completion import cmd_completion

    bash = cmd_completion("bash")
    assert "complete -F _failpack failpack" in bash
    assert "promote" in bash
    assert "rename" in bash
    assert "explain" in bash
    assert "diff" in bash
    assert "--fast" in bash
    assert "--claude-hermetic" in bash
    assert "--cursor-hermetic" in bash
    assert "packs" in bash
    zsh = cmd_completion("zsh")
    assert "#compdef failpack" in zsh
    assert "_failpack" in zsh
    assert "explain" in zsh
    assert "diff" in zsh
    assert "--fast" in zsh
    assert "--claude-hermetic" in zsh
    assert "--cursor-hermetic" in zsh
    with pytest.raises(ValueError, match="Unsupported shell"):
        cmd_completion("fish")


def test_cli_completion_and_lifecycle_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["completion", "bash"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "complete -F _failpack" in out

    parser = build_parser()
    names: set[str] = set()
    promote_help = None
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        names.update(action.choices.keys())
        if "promote" in action.choices:
            promote_help = action.choices["promote"].format_help()
    assert {"rm", "rename", "completion", "explain", "diff", "packs"} <= names
    assert promote_help is not None
    assert "--dry-run" in promote_help
    assert "--suggest" in promote_help
    assert "--write" in promote_help


def test_cli_rm_rename(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _capture_and_promote(workspace, pack_id="life-a")
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "rm", "life-a"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "golden" in err

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "rename", "life-a", "life-b"])
    assert exc.value.code == 0
    assert (workspace / ".failpack" / "packs" / "life-b").is_dir()

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "rm", "life-b", "--force"])
    assert exc.value.code == 0
    assert not (workspace / ".failpack" / "packs" / "life-b").exists()


def test_lint_ok_on_shipped_and_workspace(workspace: Path) -> None:
    from failpack.commands_lint import cmd_lint

    repo_report = cmd_lint(root=REPO)
    assert repo_report.ok, "\n".join(repo_report.summary_lines())
    assert len(repo_report.checked) >= 4

    _capture_and_promote(workspace, pack_id="lint-me")
    report = cmd_lint("lint-me", root=workspace)
    assert report.ok, "\n".join(report.summary_lines())


def test_lint_fails_on_bad_schema(workspace: Path) -> None:
    from failpack.commands_lint import cmd_lint

    _capture_and_promote(workspace, pack_id="lint-bad")
    path = workspace / ".failpack" / "packs" / "lint-bad" / "assertions.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["mystery_kind"] = [{"path": "x"}]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    report = cmd_lint("lint-bad", root=workspace)
    assert not report.ok
    assert any("mystery_kind" in i.message for i in report.issues)


def test_lint_fails_when_meta_id_mismatches(workspace: Path) -> None:
    from failpack.commands_lint import cmd_lint
    from failpack.pack import read_meta, write_meta

    _capture_and_promote(workspace, pack_id="lint-id")
    pack = workspace / ".failpack" / "packs" / "lint-id"
    meta = read_meta(pack)
    meta["id"] = "other-id"
    write_meta(pack, meta)
    report = cmd_lint("lint-id", root=workspace)
    assert not report.ok
    assert any("meta.id" in i.message for i in report.issues)


def test_report_markdown_all_and_github(
    workspace: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from failpack.commands_report import cmd_report, render_report_markdown

    _capture_and_promote(workspace, pack_id="rep-a")
    result = cmd_report(root=workspace)
    assert result.ok
    assert "# FailPack replay" in result.markdown
    assert "| Pack | Result | Checks |" in result.markdown
    assert "`rep-a`" in result.markdown
    assert "**RESULT: PASS**" in result.markdown

    one = cmd_report("rep-a", root=workspace)
    assert one.ok
    assert "FailPack replay: rep-a" in one.markdown

    summary = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    gh = cmd_report(root=workspace, github=True)
    assert gh.ok
    assert summary.is_file()
    assert "FailPack replay" in summary.read_text(encoding="utf-8")

    out = tmp_path / "out.md"
    file_report = cmd_report(root=workspace, output=out)
    assert file_report.ok
    assert out.is_file()

    # Failure markdown includes FAIL section
    pack = workspace / ".failpack" / "packs" / "rep-a"
    (pack / "artifacts" / "error.txt").write_text("mutated\n", encoding="utf-8")
    bad = cmd_report("rep-a", root=workspace, show_diff=False)
    assert not bad.ok
    assert "## Failures" in bad.markdown
    assert "**FAIL**" in bad.markdown
    assert "STORY:" in bad.markdown
    assert "failpack explain" in bad.markdown
    # render helper covers empty all-report
    empty_md = render_report_markdown(
        __import__("failpack.commands_replay", fromlist=["ReplayAllReport"]).ReplayAllReport()
    )
    assert "No golden packs" in empty_md


def test_cli_report_and_lint(
    workspace: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _capture_and_promote(workspace, pack_id="cli-rep")
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "report"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "| Pack | Result |" in out

    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "lint"])
    assert exc.value.code == 0
    assert "RESULT: PASS" in capsys.readouterr().out

    summary = tmp_path / "gha.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "report", "--github"])
    assert exc.value.code == 0
    assert summary.is_file()

    parser = build_parser()
    names: set[str] = set()
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        names.update(action.choices.keys())
    assert {"report", "lint"} <= names


def test_action_readme_documents_report_lint() -> None:
    readme = REPO / ".github" / "actions" / "failpack-replay" / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "step-summary" in text
    assert "run-lint" in text
    assert "failpack report" in text
    assert "failpack lint" in text


def test_tool_denied_and_bash_output_helpers() -> None:
    events = load_jsonl(FIXTURE_TOOL_DENIED)
    assert denied_tool_names(events) == ["Bash"]
    assert tool_denied_contains(events, "Bash")
    assert tool_denied_contains(events, "ash")  # substring
    assert not tool_denied_contains(events, "Write")
    assert bash_output_contains(events, "pyproject.toml", match="any")
    assert bash_output_contains(events, "Tool use denied: Bash", match="last")
    assert not bash_output_contains(events, "pyproject.toml", match="last")


def test_tool_denied_fixture_promotes_and_replays(workspace: Path) -> None:
    _capture_and_promote(workspace, FIXTURE_TOOL_DENIED, DEMO_TOOL_DENIED)
    pack = workspace / ".failpack" / "packs" / DEMO_TOOL_DENIED
    assertions_path = pack / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    assert data["exit_code"] == 126
    data["tool_denied_contains"] = [{"contains": "Bash"}]
    data["bash_output_contains"] = [
        {"contains": "Tool use denied: Bash", "match": "last"},
        {"contains": "pyproject.toml", "match": "any"},
    ]
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    report = cmd_replay(DEMO_TOOL_DENIED, root=workspace)
    assert report.ok, "\n".join(report.summary_lines())
    assert any(c.name.startswith("tool_denied_contains:") and c.ok for c in report.checks)
    assert any(c.name.startswith("bash_output_contains:") and c.ok for c in report.checks)

    # Break tool_denied assert
    data["tool_denied_contains"] = [{"contains": "NotARealTool"}]
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    bad = cmd_replay(DEMO_TOOL_DENIED, root=workspace)
    assert not bad.ok
    assert any(
        c.name.startswith("tool_denied_contains:") and not c.ok for c in bad.checks
    )


def test_bash_output_contains_fail_modes(workspace: Path) -> None:
    _capture_and_promote(workspace, FIXTURE_TOOL_DENIED, DEMO_TOOL_DENIED)
    pack = workspace / ".failpack" / "packs" / DEMO_TOOL_DENIED
    assertions_path = pack / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data["bash_output_contains"] = [{"contains": "THIS_NEVER_APPEARS", "match": "any"}]
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    report = cmd_replay(DEMO_TOOL_DENIED, root=workspace)
    assert not report.ok
    assert any(
        c.name.startswith("bash_output_contains:") and not c.ok for c in report.checks
    )


def test_cli_show_json(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(REPO), "show", DEMO_TOOL_DENIED, "--json"])
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pack_id"] == DEMO_TOOL_DENIED
    assert payload["status"] == "golden"
    assert payload["promoted_at"]
    assert payload["artifacts"]


def test_action_readme_documents_inputs() -> None:
    readme = REPO / ".github" / "actions" / "failpack-replay" / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "install-from" in text
    assert "run-doctor" in text
    assert "json" in text
    assert "Inputs" in text
    assert "Outputs" in text or "exit" in text.lower()
    assert "step-summary" in text
    assert "run-lint" in text


def test_shipped_demo_tool_denied_has_new_asserts() -> None:
    assertions = yaml.safe_load(
        (REPO / ".failpack" / "packs" / DEMO_TOOL_DENIED / "assertions.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert assertions["tool_denied_contains"]
    assert assertions["bash_output_contains"]
    report = cmd_replay(DEMO_TOOL_DENIED, root=REPO)
    assert report.ok, "\n".join(report.summary_lines())


def test_suggest_assertions_includes_tool_denied(workspace: Path) -> None:
    cmd_capture(FIXTURE_TOOL_DENIED, pack_id="suggest-me", root=workspace)
    pack = workspace / ".failpack" / "packs" / "suggest-me"
    meta = read_meta(pack)
    suggested = suggest_assertions(pack, meta)
    assert suggested["exit_code"] == 126
    assert suggested["fingerprints"]
    assert any(
        (e if isinstance(e, str) else e.get("contains")) == "Bash"
        for e in suggested["tool_denied_contains"]
    )
    assert suggested["bash_output_contains"]
    # Preview only — no write
    result = cmd_promote("suggest-me", root=workspace, suggest=True)
    assert isinstance(result, dict)
    assert not (pack / "assertions.yaml").exists()
    # Apply with --write
    written = cmd_promote("suggest-me", root=workspace, suggest=True, write=True)
    assert not isinstance(written, dict)
    assert (pack / "assertions.yaml").is_file()
    report = cmd_replay("suggest-me", root=workspace)
    assert report.ok, "\n".join(report.summary_lines())


def test_cli_promote_suggest_and_write(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cmd_capture(FIXTURE_TOOL_DENIED, pack_id="cli-suggest", root=workspace)
    with pytest.raises(SystemExit) as exc:
        main(["--root", str(workspace), "promote", "--suggest", "cli-suggest"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Suggested assertions" in out
    assert "tool_denied_contains" in out
    assert "exit_code" in out
    pack = workspace / ".failpack" / "packs" / "cli-suggest"
    assert not (pack / "assertions.yaml").exists()

    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--root",
                str(workspace),
                "promote",
                "--suggest",
                "--write",
                "cli-suggest",
            ]
        )
    assert exc.value.code == 0
    assert "Promoted" in capsys.readouterr().out
    assert (pack / "assertions.yaml").is_file()


def _fake_cursor_home(tmp_path: Path) -> Path:
    """Build fake $HOME with ~/.cursor/projects/.../agent-transcripts (never real ~/.cursor)."""
    home = tmp_path / "fake-cursor-home"
    session = "11111111-2222-3333-4444-555555555555"
    agent_root = home / ".cursor" / "projects" / "demo-slug" / "agent-transcripts"
    older_dir = agent_root / "00000000-0000-0000-0000-000000000000"
    newer_dir = agent_root / session
    older_dir.mkdir(parents=True)
    newer_dir.mkdir(parents=True)
    (older_dir / "00000000-0000-0000-0000-000000000000.jsonl").write_text(
        FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    # Subagent created first (older mtime) so main session wins as newest
    sub = newer_dir / "subagents"
    sub.mkdir()
    (sub / "subagent.jsonl").write_text(
        FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    time.sleep(0.05)
    (newer_dir / f"{session}.jsonl").write_text(
        FIXTURE_WRONG_CMD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return home


def test_find_cursor_latest_uses_home_fixture(tmp_path: Path) -> None:
    home = _fake_cursor_home(tmp_path)
    found = find_cursor_latest(home=home)
    assert found.name.endswith(".jsonl")
    assert "11111111-2222-3333-4444-555555555555" in found.as_posix()
    assert "subagents" not in found.parts
    assert found.is_relative_to(home / ".cursor" / "projects")


def test_capture_cursor_latest_with_fake_home(workspace: Path, tmp_path: Path) -> None:
    home = _fake_cursor_home(tmp_path)
    pack = cmd_capture(
        None,
        pack_id="cursor-latest-pack",
        root=workspace,
        cursor_latest=True,
        home=home,
    )
    meta = read_meta(pack)
    assert meta["id"] == "cursor-latest-pack"
    assert meta["exit_code"] == 4
    assert meta["source_transcript"].startswith("<cursor-latest:")


def test_cli_capture_cursor_latest_honors_HOME(
    workspace: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _fake_cursor_home(tmp_path)
    monkeypatch.setenv("HOME", str(home))
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--root",
                str(workspace),
                "capture",
                "--cursor-latest",
                "--id",
                "via-cursor-cli",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "via-cursor-cli" in out
    meta = read_meta(workspace / ".failpack" / "packs" / "via-cursor-cli")
    assert meta["exit_code"] == 4


def test_cursor_latest_missing_projects_dir(tmp_path: Path) -> None:
    empty_home = tmp_path / "empty-cursor-home"
    empty_home.mkdir()
    with pytest.raises(
        FileNotFoundError,
        match=r"cursor-hermetic|demo --fast|one-shot|\.cursor/projects",
    ):
        find_cursor_latest(home=empty_home)


def test_cursor_latest_empty_agent_transcripts(tmp_path: Path) -> None:
    home = tmp_path / "empty-agent-home"
    (home / ".cursor" / "projects" / "slug" / "agent-transcripts").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match=r"cursor-hermetic|No Cursor agent"):
        find_cursor_latest(home=home)


def test_cursor_latest_conflicts_with_claude_latest(workspace: Path, tmp_path: Path) -> None:
    home = _fake_cursor_home(tmp_path)
    with pytest.raises(ValueError, match="only one"):
        resolve_transcript_path(
            None, claude_latest=True, cursor_latest=True, home=home
        )


def test_promote_writes_tool_denied_for_fixture(workspace: Path) -> None:
    """Smarter promote should auto-include tool_denied when transcript has it."""
    _capture_and_promote(workspace, FIXTURE_TOOL_DENIED, "auto-tool")
    data = yaml.safe_load(
        (workspace / ".failpack" / "packs" / "auto-tool" / "assertions.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert data.get("tool_denied_contains")
    assert data.get("bash_output_contains")
    report = cmd_replay("auto-tool", root=workspace)
    assert report.ok, "\n".join(report.summary_lines())
