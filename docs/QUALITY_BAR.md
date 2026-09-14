# Quality bar — “done enough to sell”

Internal checklist. Not marketing copy. Honest gaps between “works for a
curious stranger on GitHub” and “comfortable asking someone to pay.”

Status as of **1.5.8**: product loop is real (`demo --fast` → capture →
promote → replay → CI Action). **Hermetic Claude one-shot** is pip-first:
`failpack demo --claude-hermetic` (bundled fixture; no clone / no live Claude).
Support path is stated. **PyPI is live** (`pip install failpack` since 1.5.5).
Static homepage + Pages workflow shipped — do **not** claim the site is live
if it 404s. Sell-ready still needs the open items below.

## Must-have before asking for money

| Gap | Why it blocks | Notes |
|---|---|---|
| **PyPI token + first upload** ✅ | Strangers expect `pip install failpack`. | **Done in 1.5.5:** first upload live on [PyPI](https://pypi.org/project/failpack/). Lead docs with `pip install failpack` + `failpack demo --fast` (+ `demo --claude-hermetic`); git install is fallback only. Do not re-upload from agents without a human-held token. |
| **Hermetic Claude one-shot** ✅ | Stranger/CI must prove `capture --claude-latest` without a live agent or invented “user” packs. | **Done in 1.5.7** (pytest + checkout script); **pip-first in 1.5.8:** `failpack demo --claude-hermetic` ships the fixture in the wheel. Thin alias: [`examples/claude-latest-hermetic.sh`](../examples/claude-latest-hermetic.sh). Doctor / capture tip the CLI path first when no sessions. |
| **Real-user packs** | Shipped goldens are fixtures. Sell story needs ≥1 pack from a stranger’s actual Claude/Cursor failure, exported and replayed cleanly. | Track anonymized exports under a private stash; do not invent “user” packs. Still open. |
| **One unpaid stranger walkthrough** | Someone who did not write FailPack should finish install → `demo --fast` → optional `demo --claude-hermetic` / `capture --claude-latest` without a Slack babysitter. | Use `examples/STRANGER_WALKTHROUGH.md`; capture friction notes, fix bugs only. Agent may reduce friction (hermetic CLI); unpaid human still open. |
| **Support path** ✅ | Paid users need somewhere to yell. | **Done in 1.5.2:** GitHub Issues + email `8725598a@gmail.com` (JiangSkirk) in [`SUPPORT.md`](SUPPORT.md) / README / CONTRIBUTING. No Discord. |

## Nice-to-have (does not block a soft launch)

| Gap | Why it helps |
|---|---|
| TestPyPI dry-run of the exact release tag | Confirms long description / classifiers before real PyPI. |
| Homepage that is not just the README ✅ | **Done in 1.5.5 (workflow shipped):** static `site/` + `.github/workflows/pages.yml`. Expected URL: [https://jiangskirk.github.io/failpack/](https://jiangskirk.github.io/failpack/). If Pages is still dark / 404, that is a **one-time** Settings flip (not a product gap): repo **Settings → Pages → Source: GitHub Actions**, then re-run the workflow (or push to `main`). Do **not** claim the site is live until that flip is done. Quickstart leads with `pip install failpack` + `failpack demo --fast` (+ hermetic CLI). |
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
failpack demo --claude-hermetic
failpack list --json
failpack diff demo-five-minute   # or any golden id
failpack lint
failpack replay --all
pytest -q
```

`demo --fast` / `demo --claude-hermetic` may leave packs under
`.failpack/packs/` in a repo checkout. That is expected for the stranger wow
path; tests must tolerate the extra goldens (do not hardcode an exact pack
inventory of 4). Optional cleanup:
`failpack rm demo-five-minute --force` /
`failpack rm claude-hermetic --force`.

When the must-have table is green, freeze the tag and ship the sell page.
Until then: polish the open CLI, do not fake readiness.
