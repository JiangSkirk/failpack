# FailPack 1.5.8 — Release notes

Tag: `v1.5.8`.

## Highlights

FailPack **1.5.8** kills the biggest remaining stranger friction after 1.5.7:
hermetic Claude one-shot proof no longer needs a git clone +
`./examples/claude-latest-hermetic.sh`. A **pip-installed** stranger can run
`failpack demo --claude-hermetic` and prove `capture --claude-latest` without a
live Claude install. Action pin stays **`@v1.5.0`**. **No PyPI re-upload from
this agent.**

## Install

```bash
pip install failpack
failpack demo --fast
failpack demo --claude-hermetic
```

Git fallback (optional):

```bash
pip install "git+https://github.com/JiangSkirk/failpack.git"
```

Editable / local:

```bash
git clone https://github.com/JiangSkirk/failpack.git
cd failpack
pip install -e ".[dev]"
failpack demo --fast
failpack demo --claude-hermetic
# alias: ./examples/claude-latest-hermetic.sh
```

Requires Python **3.11+**.

## What's new since 1.5.7

### Added

- **`failpack demo --claude-hermetic`** — fake HOME + bundled
  `claude-code-failure.jsonl` → `capture --claude-latest` →
  `promote --suggest --write` → lint → replay. Clear PASS story.
- Wheel force-include for `failpack/data/claude-code-failure.jsonl` (same
  pattern as `demo-failure.jsonl`).

### Changed

- [`examples/claude-latest-hermetic.sh`](examples/claude-latest-hermetic.sh) is a
  thin wrapper around the CLI.
- Docs / walkthrough / QUALITY_BAR / site lead with pip + `demo --fast` +
  `demo --claude-hermetic`.
- Doctor / capture tips prefer the CLI path when no sessions exist.
- Version bump to **1.5.8**.
- Docs / walkthrough / site version samples → **1.5.8**.

## Verify locally

```bash
failpack --version          # failpack 1.5.8
failpack demo --fast
failpack demo --claude-hermetic
failpack list --json
failpack lint
failpack replay --all
# both must stay green with demo leftovers present:
pytest -q tests
(cd /tmp && pytest -q /path/to/failpack/tests)
```

Optional cleanup:

```bash
failpack rm demo-five-minute --force
failpack rm claude-hermetic --force
```

## Action pin

Consumers should keep:

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.5.0
```

**Why not `@v1.5.8`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative.

## Non-goals for 1.5.8

- No **live** Creem checkout / KYC / pay links (placeholder CTA only)
- No PyPI upload from this agent (1.5.5 already live; human-held token for
  future uploads)
- No coupling to Echo, Orin, titan-agent, or any live agent install
- No Action pin retarget
- No invented “user” packs; unpaid stranger walkthrough still open
- Pages enable remains a human one-time Settings flip if still 404 — do **not**
  claim the site is live

## Still open for 惊艳

- ≥1 anonymized real-user pack (not fixtures)
- Unpaid human stranger walkthrough (agent friction fixes only)
- Pages Source=GitHub Actions flip if homepage still dark

## Links

- Homepage (Pages): [https://jiangskirk.github.io/failpack/](https://jiangskirk.github.io/failpack/)
  (if 404: Settings → Pages → Source: GitHub Actions)
- PyPI: [https://pypi.org/project/failpack/](https://pypi.org/project/failpack/)
- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.8/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.8/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.8/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.8/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.8/examples/STRANGER_WALKTHROUGH.md)
- Hermetic Claude CLI: `failpack demo --claude-hermetic`
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.8/CONTRIBUTING.md)
