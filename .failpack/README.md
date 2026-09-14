# FailPack workspace

**Tip:** try `failpack demo --fast` for a ~60s wow path, or capture a real session
with `failpack capture --claude-latest` / `--cursor-latest`.

Packs live under `packs/<id>/`.

- `failpack demo --fast` — ~60s wow path (capture → promote → replay)
- `failpack demo` — full path including intentional break/restore
- `failpack doctor [--score]` — check env + layout (+ Claude/Cursor soft tips)
- `failpack list` — list packs (id, status, exit_code, promoted_at)
- `failpack show <id>` — pretty inspect (status, asserts, artifacts; `--json`)
- `failpack status <id>` — meta + assertion summary
- `failpack capture <transcript.jsonl|dir>` — ingest a failure session
- `failpack capture --claude-latest` — Claude one-shot: newest session under `~/.claude/projects`
- `failpack capture --cursor-latest` — newest Cursor agent transcript under `~/.cursor/projects`
- `failpack promote <id>` — mark golden and write smarter assertions
- `failpack promote --suggest <id>` — preview recommended assertions (add `--write` to apply)
- `failpack watch <transcript>` — capture → promote → replay (local; same STORY/next: on FAIL)
- `failpack replay <id>` / `failpack replay --all` — verify assertions in CI
- `failpack explain <id>` — short FAIL story (+ next: promote --suggest / re-promote)
- `failpack migrate` — stamp pack schema_version (no-op if current)
