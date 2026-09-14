# FailPack pack templates & goldens

Ship these under `.failpack/packs/` as regression memory. Each golden teaches one
failure class — copy the fixture, capture your own session, or start from
`failpack demo`.

## Shipped goldens (4) + demo path (5th)

| # | Pack / path | Failure class | Fixture | What CI remembers |
|---|---|---|---|---|
| 1 | **`demo-missing-import`** | Forgotten import → `NameError` | `fixtures/claude-code-failure.jsonl` | exit `1` + error fingerprint / substring |
| 2 | **`demo-wrong-test-cmd`** | Wrong pytest target (missing file) | `fixtures/claude-code-wrong-test-cmd.jsonl` | exit `4` |
| 3 | **`demo-permission-denied`** | Wrote under `/etc/…` → `PermissionError` | `fixtures/claude-code-permission-denied.jsonl` | exit `13` + permission signal |
| 4 | **`demo-tool-denied`** | Bash network install denied by policy | `fixtures/claude-code-tool-denied.jsonl` | exit `126` + `tool_denied_contains` / `bash_output_contains` |
| 5 | **`demo-five-minute`** *(via `failpack demo [--fast]`)* | Same class as #1 — **~60s wow path**, not a permanent ship | bundled `failpack/data/demo-failure.jsonl` | teaches capture → promote → replay (+ optional intentional FAIL) |

Replay everything shipped:

```bash
failpack replay --all
failpack show demo-tool-denied
```

## How to use a template

```bash
# copy a fixture into a new pack id
failpack capture fixtures/claude-code-failure.jsonl --id my-missing-import
failpack promote my-missing-import
failpack replay my-missing-import

# or start from a real Claude Code session
failpack capture --claude-latest --id my-failure
failpack promote my-failure
failpack replay my-failure
```

When replay FAILs:

```bash
failpack explain my-failure   # what broke / which assert / what next
```

## Pack layout reminder

```
.failpack/packs/<id>/
  meta.json
  transcript.jsonl
  artifacts/          # exit_code, error, written files, digest
  expected/           # promote-time text snapshots (FAIL diffs)
  assertions.yaml
```

See the root [README](../README.md) for the five-minute path and CI Action snippet.
