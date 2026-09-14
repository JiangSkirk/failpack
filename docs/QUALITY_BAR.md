# Quality bar — “done enough to sell”

Internal checklist. Not marketing copy. Honest gaps between “works for a
curious stranger on GitHub” and “comfortable asking someone to pay.”

Status as of **1.5.0**: product loop is real (`demo --fast` → capture →
promote → replay → CI Action). Sell-ready still needs the items below.

## Must-have before asking for money

| Gap | Why it blocks | Notes |
|---|---|---|
| **PyPI token + first upload** | Strangers expect `pip install failpack`. Git install works; discovery and trust do not. | Packaging is ready (`docs/PUBLISH.md`). **Do not upload without a token in env.** |
| **Real-user packs** | Shipped goldens are fixtures. Sell story needs ≥1 pack from a stranger’s actual Claude/Cursor failure, exported and replayed cleanly. | Track anonymized exports under a private stash; do not invent “user” packs. |
| **One unpaid stranger walkthrough** | Someone who did not write FailPack should finish install → `demo --fast` → optional `capture --claude-latest` without a Slack babysitter. | Use `examples/STRANGER_WALKTHROUGH.md`; capture friction notes, fix bugs only. |
| **Support path** | Paid users need somewhere to yell. | GitHub Issues is fine for open; Personal/Team needs a stated channel (email or Discord) before charging. |

## Nice-to-have (does not block a soft launch)

| Gap | Why it helps |
|---|---|
| TestPyPI dry-run of the exact release tag | Confirms long description / classifiers before real PyPI. |
| Homepage that is not just the README | Landing copy lives in `docs/LANDING.md`; still needs a URL strangers can share. |
| Private pack vault / team dashboard | Monetization sketch in `MONETIZATION.md` — **not** in this CLI cut. |
| Windows CI smoke | Linux/macOS are the happy path; Windows is unverified. |

## Explicitly out of scope (do not block on these)

- Creem / checkout / paid tiers in-tree
- Echo / Orin / titan-agent (or any live agent) coupling
- “Stunning” marketing rewrite of the CLI
- PyPI upload from CI without a human-held token

## Smoke before every quality freeze

```bash
failpack --version
failpack doctor --score
failpack demo --fast
failpack list --json
failpack diff demo-five-minute   # or any golden id
failpack lint
failpack replay --all
pytest -q
```

When the must-have table is green, freeze the tag and ship the sell page.
Until then: polish the open CLI, do not fake readiness.
