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
failpack --version
failpack doctor
```

`failpack doctor` checks Python version, PyYAML, `.failpack/` layout, and pack counts, and prints fixes when something is missing.

## What you get (v0.2)

| Command | What it does |
|---|---|
| `failpack init` | Create `.failpack/` layout |
| `failpack doctor` | Check env + workspace; print actionable fixes |
| `failpack list` | List packs (id, status, exit_code, promoted_at) |
| `failpack status <id>` | Show meta + assertion summary for one pack |
| `failpack capture <transcript.jsonl\|dir>` | Ingest a Claude-Code-like JSONL into `.failpack/packs/<id>/` |
| `failpack promote <id>` | Mark golden + write `assertions.yaml` |
| `failpack replay <id>` | Verify assertions; **exit 0** on pass, **non-zero** on fail |
| `failpack replay --all` | Replay every golden pack; **exit non-zero** if any fail |

Shipped golden packs:

- **`demo-missing-import`** — agent forgot an import; tests fail with `NameError`
- **`demo-wrong-test-cmd`** — agent ran pytest on a missing file (`exit_code=4`)

## Quickstart

```bash
# from this repo
pip install -e ".[dev]"
failpack doctor
failpack list
failpack replay --all                 # exits 0 when all golden packs pass
failpack status demo-missing-import
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
```

Break a golden assertion (or mutate an artifact under `.failpack/packs/<id>/artifacts/`) and `failpack replay` exits non-zero — that is the CI signal.

### CI

See [`.github/workflows/failpack-replay.yml`](.github/workflows/failpack-replay.yml): install → doctor → pytest → `failpack replay --all`.

## Pack layout

```
.failpack/
  packs/<id>/
    meta.json
    transcript.jsonl
    artifacts/          # exit_code, error, written files, digest
    assertions.yaml     # written by promote
```

Assertions cover:

- **exit code** from the captured session
- **SHA-256 fingerprints** of key artifacts
- **expected substrings** (e.g. the distinctive error line)
- **optional `min_events`** — fail if the session is shorter than expected
- **optional `glob_fingerprint`** — combined hash of `artifacts/files/**` (when files were written)

Older packs without `min_events` / `glob_fingerprint` still replay.

## How money works later

Teams pay for **private packs** and a **team dashboard**, not for the open CLI core.

| Tier | Price (narrative) | What you get |
|---|---|---|
| Personal | **$19**/mo | Private packs, sync, basic history |
| Team | **$79–149**/mo | Shared packs, dashboard, seat controls |

Checkout / MoR: plan on **Creem** or **Paddle** (merchant of record). **Do not assume Polar works for mainland China payout** — pick a MoR that can actually settle to your bank/region.

Details and landing copy: [`MONETIZATION.md`](MONETIZATION.md).

## Non-goals

- **Not Stet** — FailPack does not freeze or snapshot whole agent runtimes.
- **Not Agentshield** — FailPack is not a security scanner, policy gate, or prompt firewall.
- **Not your agent** — zero coupling to Echo, Orin, titan-agent, or any live agent install. Fixtures only.

## Development

```bash
pip install -e ".[dev]"
pytest -q
failpack --help
failpack doctor
```

Requires Python 3.11+.

## License

MIT
