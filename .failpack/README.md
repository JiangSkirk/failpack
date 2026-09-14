# FailPack workspace

Packs live under `packs/<id>/`.

- `failpack doctor` — check env + this layout
- `failpack list` — list packs (id, status, exit_code, promoted_at)
- `failpack status <id>` — meta + assertion summary
- `failpack capture <transcript.jsonl|dir>` — ingest a failure session
- `failpack promote <id>` — mark golden and write assertions
- `failpack watch <transcript>` — capture → promote → replay (local)
- `failpack replay <id>` / `failpack replay --all` — verify assertions in CI
- `failpack migrate` — stamp pack schema_version (no-op if current)
