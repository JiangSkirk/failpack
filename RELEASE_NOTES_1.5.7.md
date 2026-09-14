# FailPack 1.5.7 — Release notes

Tag: `v1.5.7`.

## Highlights

FailPack **1.5.7** thickens the **Claude Code one-shot** wow path so a
stranger (and CI) can prove `capture --claude-latest` **without** a live
Claude install and **without** inventing fake “user” packs. Hermetic path:
fake HOME + `fixtures/claude-code-failure.jsonl` → promote → replay —
covered by pytest and [`examples/claude-latest-hermetic.sh`](examples/claude-latest-hermetic.sh).
Action pin stays **`@v1.5.0`**. **No PyPI re-upload from this release.**

## Install

```bash
pip install failpack
failpack demo --fast
```

Git fallback (optional):

```bash
pip install "git+https://github.com/JiangSkirk/failpack.git"
```

Editable / local (needed for the hermetic Claude script):

```bash
git clone https://github.com/JiangSkirk/failpack.git
cd failpack
pip install -e ".[dev]"
failpack demo --fast
./examples/claude-latest-hermetic.sh
```

Requires Python **3.11+**.

## What's new since 1.5.6

### Added

- Hermetic Claude one-shot e2e tests (fake HOME + shipped fixture →
  `capture --claude-latest` → promote → replay).
- [`examples/claude-latest-hermetic.sh`](examples/claude-latest-hermetic.sh) —
  one-command proof for strangers / CI.
- Doctor / capture / CLI tips when no Claude sessions: try `demo --fast` or
  the hermetic fixture path first.

### Changed

- [`examples/claude-latest-demo.md`](examples/claude-latest-demo.md) and
  [`examples/STRANGER_WALKTHROUGH.md`](examples/STRANGER_WALKTHROUGH.md) lead
  with the hermetic proof, then the real-machine one-shot.
- [`docs/QUALITY_BAR.md`](docs/QUALITY_BAR.md): hermetic Claude one-shot marked
  **done**; Pages note stays honest (404 → Settings flip; do not claim live).
  Unpaid stranger walkthrough + real-user packs still open.
- Version bump to **1.5.7**.
- Docs / walkthrough / site version samples → **1.5.7**.

## Verify locally

```bash
failpack --version          # failpack 1.5.7
failpack demo --fast
./examples/claude-latest-hermetic.sh
failpack list --json
failpack lint
failpack replay --all
# both must stay green with demo leftover present:
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

**Why not `@v1.5.7`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative.

## Non-goals for 1.5.7

- No **live** Creem checkout / KYC / pay links (placeholder CTA only)
- No PyPI re-upload (1.5.5 already live; this cut is quality / hermetic proof)
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
- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.7/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.7/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.7/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.7/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.7/examples/STRANGER_WALKTHROUGH.md)
- Hermetic Claude one-shot: [examples/claude-latest-hermetic.sh](https://github.com/JiangSkirk/failpack/blob/v1.5.7/examples/claude-latest-hermetic.sh)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.7/CONTRIBUTING.md)
