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
- `failpack export <id>` / `failpack import <pack.tgz>` — share packs
- `failpack watch <transcript>` — capture → promote → replay (local)
- `failpack replay <id>` / `failpack replay --all` — verify assertions in CI
- `failpack migrate` — stamp pack schema_version (no-op if current)
