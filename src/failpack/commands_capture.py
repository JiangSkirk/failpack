"""failpack capture — ingest a JSONL transcript into a pack."""

from __future__ import annotations

import glob as globmod
import shutil
import sys
import tempfile
from pathlib import Path

from failpack.pack import utc_now_iso, write_meta
from failpack.paths import ARTIFACTS_DIR, PACKS_DIR, TRANSCRIPT_NAME, failpack_dir
from failpack.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_KEY
from failpack.transcript import load_jsonl, slug_from_summary, summarize_events, write_artifacts

# Claude Code default session tree (relative to $HOME).
CLAUDE_PROJECTS_REL = Path(".claude") / "projects"


def claude_projects_dir(*, home: Path | None = None) -> Path:
    """Return ``<home>/.claude/projects`` (expandable via ``Path.home()``)."""
    base = home if home is not None else Path.home()
    return (base / CLAUDE_PROJECTS_REL).expanduser()


def find_newest_jsonl(project_dir: Path) -> Path:
    """Find the newest ``*.jsonl`` under a directory tree.

    Claude Code often stores session transcripts under ``~/.claude/projects``
    as ``*.jsonl``. ``project_dir`` may be that projects root, a single project
    folder, or any other directory that contains transcripts.
    """
    project_dir = project_dir.expanduser().resolve()
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {project_dir}")

    candidates = [p for p in project_dir.rglob("*.jsonl") if p.is_file()]
    if not candidates:
        raise FileNotFoundError(
            f"No *.jsonl transcripts under {project_dir}. "
            "Pass a directory that contains session JSONL "
            "(Claude Code tip: ~/.claude/projects), use --claude-latest, "
            "a fixture path, or --stdin."
        )
    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_claude_latest(*, home: Path | None = None) -> Path:
    """Discover the newest Claude Code session JSONL under ``~/.claude/projects``.

    ``home`` overrides ``Path.home()`` so tests can use a fake HOME fixture
    without touching a real ``~/.claude`` tree.
    """
    projects = claude_projects_dir(home=home)
    if not projects.is_dir():
        raise FileNotFoundError(
            f"Claude Code projects directory not found: {projects}. "
            "Install/use Claude Code, or pass a transcript path / --stdin. "
            "Tip: sessions usually live under ~/.claude/projects/<project>/*.jsonl."
        )
    return find_newest_jsonl(projects)


def resolve_transcript_path(
    transcript: Path | None,
    *,
    from_claude_project: Path | None = None,
    claude_latest: bool = False,
    stdin: bool = False,
    pattern: str | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the transcript file from path, glob, Claude helpers, or stdin.

    Exactly one input mode must be chosen (path/glob, --from-claude-project,
    --claude-latest, or --stdin).
    """
    modes = sum(
        [
            transcript is not None and str(transcript) != "-",
            from_claude_project is not None,
            claude_latest,
            stdin or (transcript is not None and str(transcript) == "-"),
            pattern is not None,
        ]
    )
    # path "-" is an alias for stdin; don't double-count with stdin flag
    if stdin and transcript is not None and str(transcript) == "-":
        modes -= 1
    if modes == 0:
        raise ValueError(
            "Nothing to capture. Try one of:\n"
            "  failpack demo\n"
            "  failpack capture --claude-latest --id my-failure\n"
            "  failpack capture path/to/session.jsonl --id my-failure\n"
            "  failpack capture --stdin --id my-failure < session.jsonl"
        )
    if modes > 1:
        raise ValueError(
            "Use only one of: transcript path / glob, --claude-latest, "
            "--from-claude-project, or --stdin."
        )

    if claude_latest:
        return find_claude_latest(home=home)

    if from_claude_project is not None:
        return find_newest_jsonl(from_claude_project)

    if stdin or (transcript is not None and str(transcript) == "-"):
        data = sys.stdin.buffer.read()
        if not data.strip():
            raise ValueError("stdin is empty — pipe a JSONL transcript into failpack capture")
        tmp = tempfile.NamedTemporaryFile(
            prefix="failpack-stdin-",
            suffix=".jsonl",
            delete=False,
        )
        tmp.write(data)
        tmp.close()
        return Path(tmp.name)

    if pattern is not None:
        matches = sorted(Path(p) for p in globmod.glob(pattern, recursive=True))
        files = [p for p in matches if p.is_file()]
        if not files:
            raise FileNotFoundError(f"No files matched glob: {pattern}")
        if len(files) == 1:
            return files[0].resolve()
        # Prefer newest when multiple match
        return max(files, key=lambda p: p.stat().st_mtime).resolve()

    assert transcript is not None
    raw = str(transcript)
    if any(ch in raw for ch in "*?[]"):
        matches = sorted(Path(p) for p in globmod.glob(raw, recursive=True))
        files = [p for p in matches if p.is_file()]
        if not files:
            raise FileNotFoundError(f"No files matched glob: {raw}")
        if len(files) == 1:
            return files[0].resolve()
        return max(files, key=lambda p: p.stat().st_mtime).resolve()

    path = transcript.expanduser()
    # Directory (not a .jsonl file): pick newest *.jsonl underneath.
    # Tip: Claude Code sessions often live under ~/.claude/projects.
    if path.is_dir():
        return find_newest_jsonl(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Transcript not found: {path}. "
            "Pass a .jsonl file, a directory containing *.jsonl "
            "(e.g. a Claude Code projects folder), --claude-latest, "
            "--from-claude-project, --stdin, or a glob."
        )
    return path.resolve()


def cmd_capture(
    transcript: Path | None = None,
    *,
    pack_id: str | None = None,
    root: Path | None = None,
    force: bool = False,
    from_claude_project: Path | None = None,
    claude_latest: bool = False,
    stdin: bool = False,
    pattern: str | None = None,
    home: Path | None = None,
) -> Path:
    source = resolve_transcript_path(
        transcript,
        from_claude_project=from_claude_project,
        claude_latest=claude_latest,
        stdin=stdin,
        pattern=pattern,
        home=home,
    )
    cleanup_tmp = stdin or (transcript is not None and str(transcript) == "-")

    try:
        events = load_jsonl(source)
        summary = summarize_events(events)
        pid = pack_id or slug_from_summary(summary, source)

        base = failpack_dir(root)
        if not base.is_dir():
            raise FileNotFoundError(
                f"No {base.name}/ directory under the project root. "
                "Run `failpack init` (or `failpack demo`) first."
            )

        pack = base / PACKS_DIR / pid
        if pack.exists():
            if not force:
                raise FileExistsError(
                    f"Pack '{pid}' already exists at {pack}. Use --force to overwrite."
                )
            shutil.rmtree(pack)

        pack.mkdir(parents=True)
        shutil.copy2(source, pack / TRANSCRIPT_NAME)
        write_artifacts(pack / ARTIFACTS_DIR, summary)

        source_label: str
        if cleanup_tmp:
            source_label = "<stdin>"
        elif claude_latest:
            source_label = f"<claude-latest:{source}>"
        elif from_claude_project is not None:
            source_label = str(source)
        else:
            source_label = str(source)

        write_meta(
            pack,
            {
                "id": pid,
                "status": "captured",
                SCHEMA_VERSION_KEY: CURRENT_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "source_transcript": source_label,
                "session_id": summary.get("session_id"),
                "exit_code": summary["exit_code"],
                "session_status": summary["status"],
                "event_count": summary["event_count"],
            },
        )
        return pack
    finally:
        if cleanup_tmp and source.exists():
            try:
                source.unlink()
            except OSError:
                pass
