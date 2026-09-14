# FailPack

**FailPack** turns a coding-agent **failure session** into a **golden CI regression pack**.

Capture a bad agent run once → promote it to golden → replay the assertions in CI so the same failure class cannot quietly regress.

This is **not** a security gate. It is a regression memory for agent sessions.

## Install

Requires Python **3.11+**.

```bash
# from a local checkout
pip install .

# or directly from GitHub
pip install git+https://github.com/JiangSkirk/failpack.git

# editable + tests
pip install -e ".[dev]"
```

Then confirm:

```bash
failpack --version   # → failpack 0.4.0
failpack doctor
```

`failpack doctor` checks Python version, PyYAML, `.failpack/` layout, and pack counts, and prints fixes when something is missing.

Colors are on for TTYs. Set `NO_COLOR=1` to disable (or `FORCE_COLOR=1` to force).

## What you get (v0.4)

| Command | What it does |
|---|---|
| `failpack init` | Create `.failpack/` layout |
| `failpack init --ci` | Also write a starter workflow that uses the composite action |
| `failpack doctor` | Check env + workspace; print actionable fixes |
| `failpack list` | List packs (id, status, exit_code, promoted_at) |
| `failpack status <id>` | Show meta + assertion summary for one pack |
| `failpack capture <transcript.jsonl\|dir>` | Ingest a Claude-Code-like JSONL into `.failpack/packs/<id>/` |
| `failpack promote <id>` | Mark golden + write `assertions.yaml` (+ expected text snapshots) |
| `failpack watch <transcript>` | Capture → promote → replay (local; exit 1 on fail) |
| `failpack replay <id>` | Verify assertions; **exit 0** on pass, **non-zero** on fail |
| `failpack replay --all` | Replay every golden pack; **exit non-zero** if any fail |
| `failpack replay … --json` | Machine-readable JSON (same exit codes) |
| `failpack replay … --no-diff` | Disable unified diffs under fingerprint FAIL blocks |
| `failpack migrate` | Stamp `schema_version` (no-op message if already current) |

On failure, replay prints **which check**, **expected vs actual**, and a **one-line hint**. When a **fingerprint** fails and a promote-time text snapshot exists, it also prints a **short unified diff** of expected vs actual artifact text (truncated; disable with `--no-diff`).

Shipped golden packs:

- **`demo-missing-import`** — agent forgot an import; tests fail with `NameError`
- **`demo-wrong-test-cmd`** — agent ran pytest on a missing file (`exit_code=4`)
- **`demo-permission-denied`** — agent wrote to `/etc/…` and hit `PermissionError` (`exit_code=13`)

## Quickstart

```bash
# from this repo
pip install -e ".[dev]"
failpack doctor
failpack list
failpack replay --all                 # exits 0 when all golden packs pass
failpack status demo-missing-import
failpack migrate                      # already current → polite no-op
```

Five-minute walkthrough (capture → promote → replay → intentional break → restore):

```bash
./examples/five-minute-demo.sh
```

### Capture your own failure

```bash
failpack init

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
failpack replay my-failure --json   # machine output

# one-shot local loop (useful before committing docs/fixtures)
failpack watch fixtures/claude-code-failure.jsonl --id my-failure --force
```

Break a golden assertion (or mutate an artifact under `.failpack/packs/<id>/artifacts/`) and `failpack replay` exits non-zero — that is the CI signal.

### Pre-commit

Ship a thin hook that runs `failpack replay --all`:

```bash
cp examples/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

See comments in [`examples/pre-commit-hook.sh`](examples/pre-commit-hook.sh) for a `pre-commit` framework snippet.

### CI (this repo or others)

```bash
failpack init --ci   # writes .github/workflows/failpack.yml
```

Or use the composite action with one line:

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@main
```

Full example: [`examples/other-repo-ci.yml`](examples/other-repo-ci.yml).  
Action source: [`.github/actions/failpack-replay`](.github/actions/failpack-replay).

This repo's workflow dogfoods the same action (see [`.github/workflows/failpack-replay.yml`](.github/workflows/failpack-replay.yml)).

## Pack layout

```
.failpack/
  packs/<id>/
    meta.json           # includes schema_version
    transcript.jsonl
    artifacts/          # exit_code, error, written files, digest
    expected/           # promote-time text snapshots (for FAIL diffs)
    assertions.yaml     # written by promote
```

Assertions cover:

- **exit code** from the captured session
- **SHA-256 fingerprints** of key artifacts
- **expected substrings** (e.g. the distinctive error line)
- **optional `min_events`** — fail if the session is shorter than expected
- **optional `glob_fingerprint`** — combined hash of `artifacts/files/**` (when files were written)

Older packs without `min_events` / `glob_fingerprint` / `schema_version` still replay; `failpack migrate` stamps the schema field.

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

## Development

```bash
pip install -e ".[dev]"
pytest -q
failpack --help
failpack doctor
failpack replay --all --json
failpack migrate
```

Requires Python 3.11+.

## License

MIT
