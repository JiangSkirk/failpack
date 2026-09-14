# FailPack workspace

Packs live under `packs/<id>/`.

- `failpack list` — list packs (id, status, exit_code, promoted_at)
- `failpack status <id>` — meta + assertion summary
- `failpack capture <transcript.jsonl>` — ingest a failure session
- `failpack promote <id>` — mark golden and write assertions
- `failpack replay <id>` — verify assertions in CI (hints + `--json`)
- `failpack replay --all` — replay every golden pack

Shipped goldens: `demo-missing-import`, `demo-wrong-test-cmd`, `demo-permission-denied`.
