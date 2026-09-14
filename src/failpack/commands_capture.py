"""failpack capture — ingest a JSONL transcript into a pack."""

from __future__ import annotations

import glob as globmod
import shutil
import sys
import tempfile
from pathlib import Path

from failpack.pack import utc_now_iso, write_meta
from failpack.paths import ARTIFACTS_DIR, PACKS_DIR, TRANSCRIPT_NAME, failpack_dir
from failpack.transcript import load_jsonl, slug_from_summary, summarize_events, write_artifacts


def find_newest_jsonl(project_dir: Path) -> Path:
    """Find the newest ``*.jsonl`` under a Claude Code projects directory.

    Claude Code stores session transcripts under a projects dir as ``*.jsonl``.
    ``project_dir`` may be the projects root or a single project folder.
    """
    project_dir = project_dir.expanduser().resolve()
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Claude project path not found: {project_dir}")

    candidates = [p for p in project_dir.rglob("*.jsonl") if p.is_file()]
    if not candidates:
        raise FileNotFoundError(
            f"No *.jsonl transcripts under {project_dir}. "
            "Pass a Claude Code projects directory, or use a fixture path / --stdin."
        )
    return max(candidates, key=lambda p: p.stat().st_mtime)


def resolve_transcript_path(
    transcript: Path | None,
    *,
    from_claude_project: Path | None = None,
    stdin: bool = False,
    pattern: str | None = None,
) -> Path:
    """Resolve the transcript file from path, glob, Claude project helper, or stdin.

    Exactly one input mode must be chosen (path/glob, --from-claude-project, or --stdin).
    """
    modes = sum(
        [
            transcript is not None and str(transcript) != "-",
            from_claude_project is not None,
            stdin or (transcript is not None and str(transcript) == "-"),
            pattern is not None,
        ]
    )
    # path "-" is an alias for stdin; don't double-count with stdin flag
    if stdin and transcript is not None and str(transcript) == "-":
        modes -= 1
    if modes == 0:
        raise ValueError(
            "Provide a transcript path, --from-claude-project <path>, "
            "--stdin, or a glob pattern."
        )
    if modes > 1:
        raise ValueError(
            "Use only one of: transcript path / glob, --from-claude-project, or --stdin."
        )

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
    if not path.is_file():
        raise FileNotFoundError(f"Transcript not found: {path}")
    return path.resolve()


def cmd_capture(
    transcript: Path | None = None,
    *,
    pack_id: str | None = None,
    root: Path | None = None,
    force: bool = False,
    from_claude_project: Path | None = None,
    stdin: bool = False,
    pattern: str | None = None,
) -> Path:
    source = resolve_transcript_path(
        transcript,
        from_claude_project=from_claude_project,
        stdin=stdin,
        pattern=pattern,
    )
    cleanup_tmp = stdin or (transcript is not None and str(transcript) == "-")

    try:
        events = load_jsonl(source)
        summary = summarize_events(events)
        pid = pack_id or slug_from_summary(summary, source)

        base = failpack_dir(root)
        if not base.is_dir():
            raise FileNotFoundError(
                f"No {base.name}/ directory. Run `failpack init` first."
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
        elif from_claude_project is not None:
            source_label = str(source)
        else:
            source_label = str(source)

        write_meta(
            pack,
            {
                "id": pid,
                "status": "captured",
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
