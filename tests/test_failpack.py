"""End-to-end tests for FailPack capture → promote → replay."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from failpack.commands_capture import cmd_capture
from failpack.commands_init import cmd_init
from failpack.commands_promote import cmd_promote
from failpack.commands_replay import cmd_replay
from failpack.pack import sha256_file

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "fixtures" / "claude-code-failure.jsonl"
DEMO_ID = "demo-missing-import"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    cmd_init(tmp_path)
    return tmp_path


def _capture_and_promote(workspace: Path) -> str:
    pack = cmd_capture(FIXTURE, pack_id=DEMO_ID, root=workspace)
    cmd_promote(DEMO_ID, root=workspace)
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
    assert any(not c.ok and c.name.startswith("substring:") for c in report.checks)


def test_replay_fails_when_artifact_mutated(workspace: Path) -> None:
    _capture_and_promote(workspace)
    pack = workspace / ".failpack" / "packs" / DEMO_ID
    error_path = pack / "artifacts" / "error.txt"
    original = error_path.read_text(encoding="utf-8")
    error_path.write_text(original + "\nMUTATED_BY_TEST\n", encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert not report.ok
    assert any(not c.ok and "fingerprint:artifacts/error.txt" in c.name for c in report.checks)


def test_replay_fails_when_exit_code_assertion_breaks(workspace: Path) -> None:
    _capture_and_promote(workspace)
    assertions_path = workspace / ".failpack" / "packs" / DEMO_ID / "assertions.yaml"
    data = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
    data["exit_code"] = 0
    assertions_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    report = cmd_replay(DEMO_ID, root=workspace)
    assert not report.ok
    assert any(c.name == "exit_code" and not c.ok for c in report.checks)


def test_demo_pack_in_repo_replays_clean() -> None:
    """Shipped golden pack under .failpack/packs/demo-missing-import must pass."""
    demo = REPO / ".failpack" / "packs" / DEMO_ID
    assert demo.is_dir(), "demo golden pack missing — run capture+promote in repo"
    report = cmd_replay(DEMO_ID, root=REPO)
    assert report.ok, "\n".join(report.summary_lines())


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
