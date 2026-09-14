# FailPack

**FailPack** (alt name: **Orin Replay**) turns a coding-agent **failure session** into a **golden CI regression pack**.

Capture a bad agent run once → promote it to golden → replay the assertions in CI so the same failure class cannot quietly regress.

This is **not** a security gate. It is a regression memory for agent sessions.

## What you get (v0)

| Command | What it does |
|---|---|
| `failpack init` | Create `.failpack/` layout |
| `failpack capture <transcript.jsonl>` | Ingest a Claude-Code-like JSONL into `.failpack/packs/<id>/` |
| `failpack promote <id>` | Mark golden + write `assertions.yaml` (fingerprints, substrings, exit code) |
| `failpack replay <id>` | Verify assertions; **exit 0** on pass, **non-zero** on fail |

Shipped demo pack: **`demo-missing-import`** (agent forgot an import; tests fail with `NameError`).

## Quickstart

```bash
# from this repo
uv sync --extra dev   # or: pip install -e ".[dev]"
failpack replay demo-missing-import   # exits 0

# capture → promote your own fixture
failpack init
failpack capture fixtures/claude-code-failure.jsonl --id my-failure
failpack promote my-failure
failpack replay my-failure
```

Break a golden assertion (or mutate an artifact under `.failpack/packs/<id>/artifacts/`) and `failpack replay` exits non-zero — that is the CI signal.

### CI

See [`.github/workflows/failpack-replay.yml`](.github/workflows/failpack-replay.yml): install → pytest → `failpack replay demo-missing-import`.

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
uv sync --extra dev
pytest -q
failpack --help
```

Requires Python 3.11+.

## License

MIT
