"""failpack capture — ingest a JSONL transcript into a pack."""

from __future__ import annotations

import shutil
from pathlib import Path

from failpack.pack import utc_now_iso, write_meta
from failpack.paths import ARTIFACTS_DIR, PACKS_DIR, TRANSCRIPT_NAME, failpack_dir
from failpack.transcript import load_jsonl, slug_from_summary, summarize_events, write_artifacts


def cmd_capture(
    transcript: Path,
    *,
    pack_id: str | None = None,
    root: Path | None = None,
    force: bool = False,
) -> Path:
    transcript = transcript.resolve()
    if not transcript.is_file():
        raise FileNotFoundError(f"Transcript not found: {transcript}")

    events = load_jsonl(transcript)
    summary = summarize_events(events)
    pid = pack_id or slug_from_summary(summary, transcript)

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
    shutil.copy2(transcript, pack / TRANSCRIPT_NAME)
    write_artifacts(pack / ARTIFACTS_DIR, summary)
    write_meta(
        pack,
        {
            "id": pid,
            "status": "captured",
            "created_at": utc_now_iso(),
            "source_transcript": str(transcript),
            "session_id": summary.get("session_id"),
            "exit_code": summary["exit_code"],
            "session_status": summary["status"],
            "event_count": summary["event_count"],
        },
    )
    return pack
