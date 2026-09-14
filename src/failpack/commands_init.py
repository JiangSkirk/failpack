"""failpack init — create .failpack/ layout."""

from __future__ import annotations

from pathlib import Path

from failpack.paths import FAILPACK_DIR, PACKS_DIR


def cmd_init(root: Path | None = None) -> Path:
    base = (root or Path.cwd()).resolve()
    fp = base / FAILPACK_DIR
    packs = fp / PACKS_DIR
    packs.mkdir(parents=True, exist_ok=True)
    gitkeep = packs / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    readme = fp / "README.md"
    if not readme.exists():
        readme.write_text(
            "# FailPack workspace\n\n"
            "Packs live under `packs/<id>/`.\n\n"
            "- `failpack list` — list packs (id, status, exit_code, promoted_at)\n"
            "- `failpack status <id>` — meta + assertion summary\n"
            "- `failpack capture <transcript.jsonl>` — ingest a failure session\n"
            "- `failpack promote <id>` — mark golden and write assertions\n"
            "- `failpack replay <id>` — verify assertions in CI\n",
            encoding="utf-8",
        )
    return fp
