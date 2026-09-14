"""failpack watch — capture → promote → replay (thin local wrapper)."""

from __future__ import annotations

from pathlib import Path

from failpack.commands_capture import cmd_capture
from failpack.commands_promote import cmd_promote
from failpack.commands_replay import ReplayReport, cmd_replay


def cmd_watch(
    transcript: Path | None = None,
    *,
    pack_id: str | None = None,
    root: Path | None = None,
    force: bool = False,
    from_claude_project: Path | None = None,
    claude_latest: bool = False,
    cursor_latest: bool = False,
    stdin: bool = False,
    pattern: str | None = None,
    show_diff: bool = True,
    home: Path | None = None,
) -> tuple[str, ReplayReport]:
    """Capture a transcript, promote it golden, then replay.

    Useful for pre-commit docs and local "did this failure stay golden?" checks.
    Returns ``(pack_id, replay_report)``.
    """
    pack = cmd_capture(
        transcript,
        pack_id=pack_id,
        root=root,
        force=force,
        from_claude_project=from_claude_project,
        claude_latest=claude_latest,
        cursor_latest=cursor_latest,
        stdin=stdin,
        pattern=pattern,
        home=home,
    )
    pid = pack.name
    cmd_promote(pid, root=root)
    report = cmd_replay(pid, root=root, show_diff=show_diff)
    return pid, report
