"""failpack init — create .failpack/ layout (optionally a starter CI workflow)."""

from __future__ import annotations

from pathlib import Path

from failpack.paths import FAILPACK_DIR, PACKS_DIR

CI_WORKFLOW_REL = Path(".github") / "workflows" / "failpack.yml"

CI_WORKFLOW_TEMPLATE = """\
# Written by `failpack init --ci`. Pin the action to a tag/SHA in real use.
name: FailPack regression replay

on:
  push:
  pull_request:

jobs:
  failpack:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: JiangSkirk/failpack/.github/actions/failpack-replay@main
        with:
          # This repo: install from the checkout. Other repos: omit install-from
          # (defaults to git+https://github.com/JiangSkirk/failpack.git).
          install-from: "."
          # run-doctor: "true"
          # json: "false"
"""

WORKSPACE_README = """\
# FailPack workspace

**Tip:** try `failpack demo` for a five-minute wow path, or capture a real Claude
Code session with `failpack capture --claude-latest --id my-failure`.

Packs live under `packs/<id>/`.

- `failpack demo` — one-command five-minute wow path
- `failpack doctor` — check env + this layout (+ Claude projects tip)
- `failpack list` — list packs (id, status, exit_code, promoted_at)
- `failpack show <id>` — pretty inspect (status, asserts, artifacts; `--json`)
- `failpack status <id>` — meta + assertion summary
- `failpack capture <transcript.jsonl|dir>` — ingest a failure session
- `failpack capture --claude-latest` — newest session under `~/.claude/projects`
- `failpack promote <id>` — mark golden and write assertions
- `failpack promote --dry-run <id>` — preview assertions without writing
- `failpack rename <old> <new>` — rename pack id + update meta
- `failpack rm <id> [--force]` — delete a pack (golden needs --force)
- `failpack export <id>` / `failpack import <pack.tgz>` — share packs
- `failpack watch <transcript>` — capture → promote → replay (local)
- `failpack replay <id>` / `failpack replay --all` — verify assertions in CI
- `failpack completion bash|zsh` — print shell completion script
- `failpack migrate` — stamp pack schema_version (no-op if current)
"""


def cmd_init(root: Path | None = None, *, ci: bool = False) -> tuple[Path, Path | None]:
    """Create ``.failpack/`` layout. With *ci*, also write a starter workflow.

    Returns ``(failpack_dir, ci_workflow_path_or_none)``.
    """
    base = (root or Path.cwd()).resolve()
    fp = base / FAILPACK_DIR
    packs = fp / PACKS_DIR
    packs.mkdir(parents=True, exist_ok=True)
    gitkeep = packs / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    readme = fp / "README.md"
    if not readme.exists():
        readme.write_text(WORKSPACE_README, encoding="utf-8")

    workflow_path: Path | None = None
    if ci:
        workflow_path = base / CI_WORKFLOW_REL
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        if not workflow_path.exists():
            workflow_path.write_text(CI_WORKFLOW_TEMPLATE, encoding="utf-8")
        # If it already exists, leave it alone (idempotent init).
    return fp, workflow_path
