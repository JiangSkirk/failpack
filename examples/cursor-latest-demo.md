# Demo: `failpack capture --cursor-latest`

Magic path: discover the newest Cursor agent transcript under
`~/.cursor/projects/*/agent-transcripts` and ingest it as a FailPack pack.

> **Tests and CI MUST use a fake HOME.** Never point unit tests at a real
> `~/.cursor` tree. This doc shows the real-machine flow.

## What FailPack looks for (best-effort)

Cursor layouts evolve. FailPack searches, in order of preference:

```text
~/.cursor/projects/
  └── <project-slug>/
        └── agent-transcripts/
              ├── <session-uuid>/
              │     ├── <session-uuid>.jsonl     # main session ← preferred
              │     └── subagents/<uuid>.jsonl   # spawned agents
              └── older-flat.jsonl               # older flat layout
```

`--cursor-latest` picks the newest `*.jsonl` under those trees (preferring a
main session over `subagents/` when mtimes tie).

If `~/.cursor/projects` is missing, or no `*.jsonl` is found, FailPack prints a
clear **not found** message and points here — it does not invent paths.

## Prerequisites

```bash
pip install "git+https://github.com/JiangSkirk/failpack.git"
# or from a checkout: pip install -e ".[dev]"
failpack --version    # failpack 1.5.4+
failpack doctor --score
failpack init         # if this repo isn't already initialized
```

## Screenshots-as-text

### 1) Capture the newest Cursor agent transcript

```bash
$ failpack capture --cursor-latest --id cursor-latest-demo --force
Captured pack 'cursor-latest-demo' → /…/.failpack/packs/cursor-latest-demo
```

Equivalent explicit forms:

```bash
failpack capture ~/.cursor/projects --id cursor-latest-demo --force
# or a known export:
failpack capture ~/exports/cursor-agent-fail.jsonl --id cursor-latest-demo --force
```

### 2) Suggest assertions → write → replay

```bash
$ failpack promote --suggest cursor-latest-demo
# Suggested assertions for 'cursor-latest-demo'
# Analyzed: artifacts + transcript events (ticks)
# …
# Apply with: failpack promote --suggest --write cursor-latest-demo

$ failpack promote --suggest --write cursor-latest-demo
Promoted pack 'cursor-latest-demo' to golden (…/assertions.yaml)

$ failpack replay cursor-latest-demo
RESULT: PASS
```

### 3) Not found (expected when Cursor isn't installed)

```bash
$ failpack capture --cursor-latest --id missing
error: Cursor projects directory not found: /home/you/.cursor/projects. …
See examples/cursor-latest-demo.md.
```

Or when the tree exists but has no transcripts:

```bash
error: No Cursor agent *.jsonl transcripts under /home/you/.cursor/projects. …
```

## Fake-HOME tip for contributors

```bash
# never point tests at a real ~/.cursor
export HOME=/tmp/failpack-fake-home
SESSION=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
mkdir -p "$HOME/.cursor/projects/demo/agent-transcripts/$SESSION"
cp fixtures/claude-code-failure.jsonl \
  "$HOME/.cursor/projects/demo/agent-transcripts/$SESSION/$SESSION.jsonl"
failpack capture --cursor-latest --id from-fake-home --force
```

Claude-compatible JSONL fixtures work for layout tests. Real Cursor exports may
differ slightly; FailPack is best-effort on format — if parse fails, export a
Claude-Code-like JSONL or pass an explicit path.

See also: [`claude-latest-demo.md`](claude-latest-demo.md),
[`STRANGER_WALKTHROUGH.md`](STRANGER_WALKTHROUGH.md),
[`five-minute-demo.sh`](five-minute-demo.sh).
