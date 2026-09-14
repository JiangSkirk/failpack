# FailPack

[![FailPack replay](https://github.com/JiangSkirk/failpack/actions/workflows/failpack-replay.yml/badge.svg)](https://github.com/JiangSkirk/failpack/actions/workflows/failpack-replay.yml)
[![version](https://img.shields.io/badge/version-1.5.5-blue.svg)](https://github.com/JiangSkirk/failpack/releases)

**FailPack** is regression memory for coding-agent failures.

Agents fail once in odd ways — missing imports, wrong test commands, denied
tools. Chat history forgets; FailPack does not. Capture the bad session,
promote golden assertions, replay them on every PR so the same failure class
cannot quietly come back.

Not a security gate. A boring, repeatable CI signal.

**Landing (GitHub Pages):** [https://jiangskirk.github.io/failpack/](https://jiangskirk.github.io/failpack/)
(static `site/` — Privacy / Terms + waitlist; not a live storefront).

## ~60-second path

```bash
# once on PyPI (preferred when published)
pip install failpack

# works today — git fallback
pip install "git+https://github.com/JiangSkirk/failpack.git"

failpack demo --fast
```

That is the whole product loop: **install → `demo --fast`**. Prefer `--fast`
for strangers; plain `failpack demo` adds doctor + intentional break/restore.
Optional next steps after the wow:

```bash
failpack doctor --score              # 0–100 readiness + checklist
failpack capture --claude-latest --id my-failure   # Claude Code one-shot
failpack capture --cursor-latest --id cursor-fail
failpack promote --suggest my-failure
failpack promote --suggest --write my-failure
failpack replay my-failure
failpack explain my-failure          # when something FAILs
failpack diff my-failure             # expected vs actual (no full replay)
```

## Install

Requires Python **3.11+**.

```bash
# preferred once published to PyPI
pip install failpack

# git fallback (works today; no PyPI token required)
pip install "git+https://github.com/JiangSkirk/failpack.git"

# from a local checkout (editable + tests)
pip install -e ".[dev]"

# or with uv
uv pip install -e ".[dev]"
```

First command after install:

```bash
failpack demo --fast     # ~60s wow (recommended)
# failpack demo          # full path with break/restore
```

Then confirm readiness:

```bash
failpack --version          # → failpack 1.5.5
failpack doctor --score     # 0–100 + checklist (exit 0 unless --strict)
```

Stranger copy-paste session: [`examples/STRANGER_WALKTHROUGH.md`](examples/STRANGER_WALKTHROUGH.md).

## Support

Bugs and friction: open a **[GitHub Issue](https://github.com/JiangSkirk/failpack/issues)**.
Private contact: email `8725598a@gmail.com` (owner **JiangSkirk**). Details:
[`docs/SUPPORT.md`](docs/SUPPORT.md).

`failpack doctor` checks Python, PyYAML, soft Claude / Cursor project paths, `.failpack/` layout, and pack counts — with tips like `capture --claude-latest` / `--cursor-latest` when sessions are found. `--score` adds a readiness score over **python**, **packs_dir**, **claude_projects**, **cursor_projects**, **lint**, and **golden_count**. Agent paths are soft (+5 each); missing both still yields **90/100** in CI. Doctor exits **0** by default; pass `--strict` to fail the process when checks FAIL.

Colors are on for TTYs. Set `NO_COLOR=1` to disable (or `FORCE_COLOR=1` to force).

## Daily loop

The everyday failure → golden → gate cycle:

```bash
failpack capture --claude-latest --id my-failure   # or --cursor-latest / path
failpack promote --suggest my-failure              # preview asserts
failpack promote --suggest --write my-failure      # apply when they look right
failpack replay my-failure                         # CI signal (STORY + next: on FAIL)
failpack watch fixtures/claude-code-failure.jsonl --id my-failure --force
# watch = capture → promote → replay; on FAIL prints the same STORY / next: tips
```

## What you get (v1.5)

| Command | What it does |
|---|---|
| `failpack demo` | **One-command wow:** capture → promote → replay (+ intentional break) |
| `failpack demo --fast` | **~60s stranger path:** capture → promote → replay only |
| `failpack init` | Create `.failpack/` layout (tip README → `demo` / `--claude-latest` / `--cursor-latest`) |
| `failpack init --ci` | Also write a starter workflow pinned to `@v1.5.0` (or use `@main`) |
| `failpack doctor` | Check env + Claude/Cursor projects + workspace; print actionable fixes |
| `failpack doctor --score` | **Readiness 0–100** + checklist (python / packs / claude / cursor / lint / goldens) |
| `failpack list` | Clean aligned table of packs (id, status, exit, promoted_at) |
| `failpack list --json` / `packs --json` | **Stable machine pack index** for tooling |
| `failpack show <id>` | **Pretty inspect** status, exit, asserts, artifacts (`--json`) |
| `failpack status <id>` | Show meta + assertion summary for one pack |
| `failpack capture --claude-latest` | **Claude one-shot:** newest Claude Code session under `~/.claude/projects` |
| `failpack capture --cursor-latest` | **Magic path:** newest Cursor agent transcript under `~/.cursor/projects` |
| `failpack capture <transcript.jsonl\|dir>` | Ingest a Claude-Code-like JSONL into `.failpack/packs/<id>/` |
| `failpack promote <id>` | Mark golden + write smarter `assertions.yaml` (+ expected snapshots) |
| `failpack promote --suggest <id>` | Preview recommended asserts (exit / fingerprints / tool_denied / bash) |
| `failpack promote --suggest --write <id>` | Apply suggested assertions |
| `failpack promote --dry-run <id>` | Preview assertions YAML **without** writing |
| `failpack re-promote <id>` | Refresh assertions from **current** artifacts after intentional fix |
| `failpack lint [id]` | Validate pack layout + assertion schema (no replay) |
| `failpack report [id]` | Markdown replay summary (stdout or `$GITHUB_STEP_SUMMARY`) |
| `failpack explain [id]` | **Short FAIL story:** what broke / which assert / what next |
| `failpack diff <id>` | **Expected vs actual** artifact summary (no full replay; `--json`) |
| `failpack rename <old> <new>` | Rename pack id + update meta / assertions |
| `failpack rm <id> [--force]` | Delete a pack (golden requires `--force`) |
| `failpack export <id> [-o pack.tgz]` | Share a golden pack (assertions + expected + meta + artifacts) |
| `failpack import <pack.tgz>` | Restore into `.failpack/packs/` (`--force` / `--rename`) |
| `failpack watch <transcript>` | Capture → promote → replay (local; **same STORY/`next:` on FAIL** as replay) |
| `failpack replay <id>` | Verify assertions; **exit 0** on pass, **non-zero** on fail |
| `failpack replay --all` | Replay every golden pack; **SUMMARY** of fails; exit non-zero if any fail |
| `failpack replay … --json` | Machine-readable JSON (same exit codes) |
| `failpack replay … --no-diff` | Disable unified diffs under fingerprint FAIL blocks |
| `failpack completion bash\|zsh` | Print shell completion script for power users |
| `failpack migrate` | Stamp `schema_version` (no-op message if already current) |

On failure, **replay** and **watch** print **which check**, **expected vs actual**, a **one-line hint**, a **STORY** block, and a one-line **`next:`** tip (`explain` · `diff` · `re-promote`). Prefer `failpack explain <id>` when you only want the story, or `failpack diff <id>` for expected vs actual text **without** replaying assertions. When a **fingerprint** fails and a promote-time text snapshot exists, replay also prints a **short unified diff** of expected vs actual artifact text (truncated; disable with `--no-diff`).

## Pack templates (goldens)

What each shipped pack teaches — full table in [`docs/PACKS.md`](docs/PACKS.md):

| Pack | Failure class |
|---|---|
| **`demo-missing-import`** | Agent forgot an import → `NameError` |
| **`demo-wrong-test-cmd`** | Agent ran pytest on a missing file (`exit_code=4`) |
| **`demo-permission-denied`** | Agent wrote to `/etc/…` → `PermissionError` (`exit_code=13`) |
| **`demo-tool-denied`** | Bash network install denied by policy (`exit_code=126`; `tool_denied_contains` + `bash_output_contains`) |
| **`demo-five-minute`** | Created by `failpack demo` — same class as missing-import; teaches the wow path |

## Quickstart

```bash
# from this repo
pip install -e ".[dev]"
failpack demo --fast                  # ~60s first command after install
failpack doctor --score
failpack list
failpack show demo-tool-denied        # pretty inspect (+ --json)
failpack lint
failpack replay --all                 # exits 0 when all golden packs pass
failpack status demo-missing-import
failpack migrate                      # already current → polite no-op
```

### Share a pack

```bash
failpack export demo-missing-import -o demo-missing-import.tgz
failpack import demo-missing-import.tgz --rename shared-copy
failpack replay shared-copy
```

Claude / Cursor latest magic paths (screenshots-as-text):

```bash
# see examples/claude-latest-demo.md
failpack capture --claude-latest --id my-failure
# see examples/cursor-latest-demo.md (best-effort; fake HOME in tests)
failpack capture --cursor-latest --id cursor-fail
```

### Capture your own failure

```bash
failpack init

# magic: newest Claude Code session under ~/.claude/projects
failpack capture --claude-latest --id my-failure

# magic: newest Cursor agent transcript under ~/.cursor/projects
failpack capture --cursor-latest --id cursor-fail

# path to a fixture / exported transcript
failpack capture fixtures/claude-code-failure.jsonl --id my-failure

# directory: picks the newest *.jsonl underneath
# tip: Claude Code sessions often live under ~/.claude/projects
failpack capture ~/.claude/projects --id my-failure
# same idea via explicit flag:
failpack capture --from-claude-project ~/.claude/projects --id my-failure

# or pipe JSONL on stdin
failpack capture --stdin --id my-failure < session.jsonl

# or a glob (newest match wins if several)
failpack capture --glob 'fixtures/*.jsonl' --id my-failure

failpack promote my-failure
failpack replay my-failure
failpack explain my-failure         # when FAIL: short story
failpack replay my-failure --json   # machine output

# after intentional drift / fix — refresh golden assertions
failpack re-promote my-failure

# one-shot local loop (useful before committing docs/fixtures)
failpack watch fixtures/claude-code-failure.jsonl --id my-failure --force
# or: failpack watch --claude-latest --id my-failure --force
```

Break a golden assertion (or mutate an artifact under `.failpack/packs/<id>/artifacts/`) and `failpack replay` exits non-zero — that is the CI signal. When the new signals are intentional, `failpack re-promote <id>` refreshes assertions from current artifacts.

## Pack lifecycle

Manage packs after capture without hand-editing `.failpack/packs/`:

```bash
failpack promote --suggest my-failure   # preview recommended asserts
failpack promote --suggest --write my-failure  # apply suggestions
failpack promote --dry-run my-failure   # preview assertions.yaml (no write)
failpack promote my-failure             # write smarter assertions + mark golden
failpack lint my-failure                # schema / layout validate (no replay)
failpack report                         # markdown summary (CI-friendly)
failpack report --github                # append to $GITHUB_STEP_SUMMARY
failpack explain my-failure             # STORY only (what / assert / next)
failpack rename my-failure nicer-id     # rename dir + meta.id + assertions pack_id
failpack rm nicer-id                    # refuses if golden
failpack rm nicer-id --force            # delete golden pack for real

# shell completion (optional)
eval "$(failpack completion bash)"      # or: failpack completion zsh
```

On promote / replay load, FailPack **validates** assertion kinds and required fields.
Unknown kinds (e.g. a typo’d top-level key) or missing `path` / `sha256` / `contains`
raise a clear error instead of being silently ignored. `failpack lint` surfaces the
same checks as a dedicated command.

### Cursor agent transcripts

`--cursor-latest` best-effort scans `~/.cursor/projects/*/agent-transcripts` for the
newest `*.jsonl` (main session preferred over `subagents/` on mtime ties). Tests
must use a **fake HOME**. Manual path still works:

```bash
failpack capture --cursor-latest --id cursor-fail
failpack capture /path/to/exported-session.jsonl --id cursor-fail
```

See [`examples/cursor-latest-demo.md`](examples/cursor-latest-demo.md) and
[`examples/claude-latest-demo.md`](examples/claude-latest-demo.md).

### Pre-commit

Ship a thin hook that runs `failpack replay --all`:

```bash
cp examples/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

See comments in [`examples/pre-commit-hook.sh`](examples/pre-commit-hook.sh) for a `pre-commit` framework snippet.

### CI (Action + step summary)

Copy-paste into any repo that vendors packs under `.failpack/packs/`:

```yaml
name: FailPack regression replay
on: [push, pull_request]
jobs:
  failpack:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Prefer @v1.5.0 (release pin). @main is a valid alternative.
      - uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.5.0
        with:
          # defaults (both on):
          # run-lint: "true"        # failpack lint before replay
          # step-summary: "true"    # failpack report --github → job summary
          # run-doctor: "true"      # failpack doctor --score (advisory)
          # json: "false"
```

Or generate a starter workflow (pins `@v1.5.0`; swap to `@main` if you prefer tip):

```bash
failpack init --ci   # writes .github/workflows/failpack.yml
```

**What `run-lint` does (default `true`):** runs `failpack lint` before replay — layout + assertion schema validate, no replay. Lint errors fail the job early.

**What the step summary looks like** (`failpack report --github`, default `step-summary: true`):

```markdown
# FailPack replay

| Pack | Result | Checks |
| --- | --- | --- |
| `demo-missing-import` | **PASS** | 5/5 |
| `demo-tool-denied` | **FAIL** | 4/6 |

## Failures

### `demo-tool-denied`

> STORY: Pack 'demo-tool-denied' failed 2 of 6 checks.
>   What broke: …
>   Assertion:  …
>   Next:       …

- **FAIL** `fingerprint:artifacts/error.txt`: …
```

Full example: [`examples/other-repo-ci.yml`](examples/other-repo-ci.yml).  
Action source + docs: [`.github/actions/failpack-replay`](.github/actions/failpack-replay)
([README](.github/actions/failpack-replay/README.md) covers inputs / exit codes / examples).

This repo's workflow dogfoods the same action (see [`.github/workflows/failpack-replay.yml`](.github/workflows/failpack-replay.yml)).

## Pack layout

```
.failpack/
  packs/<id>/
    meta.json           # includes schema_version
    transcript.jsonl
    artifacts/          # exit_code, error, written files, digest
    expected/           # promote-time text snapshots (for FAIL diffs)
    assertions.yaml     # written by promote / re-promote
```

Assertions cover:

- **exit code** from the captured session
- **SHA-256 fingerprints** of key artifacts
- **expected substrings** (e.g. the distinctive error line)
- **optional `min_events`** — fail if the session is shorter than expected
- **optional `glob_fingerprint`** — combined hash of `artifacts/files/**` (when files were written)
- **optional `tool_denied_contains`** — denied tool name substring in transcript/tool events
- **optional `bash_output_contains`** — Bash tool output contains string (`match: any` or `last`)

Older packs without `min_events` / `glob_fingerprint` / transcript asserts / `schema_version`
still replay; `failpack migrate` stamps the schema field.

### Transcript assertion examples

```yaml
tool_denied_contains:
  - contains: Bash          # a denied tool_use name contains this substring

bash_output_contains:
  - contains: "Permission denied"
    match: any              # default: any Bash tool_result
  - contains: "exit_code=126"
    match: last             # only the last Bash tool_result
```

## Why not Stet / AgentClash?

Honest short take:

| | **FailPack** | **Stet-like** | **AgentClash-like** |
|---|---|---|---|
| Job | Light **golden packs** from real failure sessions | Freeze / snapshot whole agent runtimes | Full harness / eval platform for agents |
| Input | One JSONL (or dir of sessions) you already have | Runtime / environment snapshots | Suites, scorers, multi-run evals |
| CI signal | Fingerprints + substrings + exit code | “Did the world drift?” | “Did the agent score regress?” |
| Weight | Small CLI + packs under `.failpack/` | Heavier runtime story | Heavier eval infra |

FailPack is intentionally narrow: **capture the failure you already saw**, promote it, and keep CI honest. It is not a full harness eval platform and not a whole-runtime freezer.

## Non-goals

- **Not Stet** — FailPack does not freeze or snapshot whole agent runtimes.
- **Not AgentClash / eval platforms** — FailPack is not a multi-run agent benchmark harness.
- **Not Agentshield** — FailPack is not a security scanner, policy gate, or prompt firewall.
- **Not your agent** — zero coupling to Echo, Orin, titan-agent, or any live agent install. Fixtures only.
- **Not a paid product surface** — no monetization in this line of work; the open CLI is the product.

## Development

```bash
pip install -e ".[dev]"
pytest -q
failpack --help
failpack doctor --score
failpack demo --skip-break
failpack lint
failpack replay --all --json
failpack migrate
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CHANGELOG.md`](CHANGELOG.md), [`docs/SUPPORT.md`](docs/SUPPORT.md), [`docs/PUBLISH.md`](docs/PUBLISH.md) (TestPyPI/PyPI steps), [`docs/QUALITY_BAR.md`](docs/QUALITY_BAR.md) (sell-ready checklist), [`RELEASE_NOTES_1.5.5.md`](RELEASE_NOTES_1.5.5.md) / [`RELEASE_NOTES_1.5.4.md`](RELEASE_NOTES_1.5.4.md) / [`RELEASE_NOTES_1.5.3.md`](RELEASE_NOTES_1.5.3.md) / [`RELEASE_NOTES_1.5.2.md`](RELEASE_NOTES_1.5.2.md) / [`RELEASE_NOTES_1.5.0.md`](RELEASE_NOTES_1.5.0.md) / [`RELEASE_NOTES_1.4.0.md`](RELEASE_NOTES_1.4.0.md) / [`RELEASE_NOTES_1.3.0.md`](RELEASE_NOTES_1.3.0.md), [`examples/STRANGER_WALKTHROUGH.md`](examples/STRANGER_WALKTHROUGH.md), and [`docs/PACKS.md`](docs/PACKS.md).

Requires Python 3.11+.

## License

MIT
