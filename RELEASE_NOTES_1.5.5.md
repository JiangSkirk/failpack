# FailPack 1.5.5 — Release notes

Tag: `v1.5.5`.

## Highlights

FailPack **1.5.5** is a small **quality-freeze** cut: ship a stranger-shareable
GitHub Pages homepage from `site/`, and sync the static Quickstart to the
current wow path (`failpack demo --fast`). Action pin stays **`@v1.5.0`**.

## Install

```bash
# once on PyPI (preferred when published)
pip install failpack

# works today — git fallback
pip install "git+https://github.com/JiangSkirk/failpack.git"

failpack demo --fast
```

Editable / local:

```bash
git clone https://github.com/JiangSkirk/failpack.git
cd failpack
pip install -e ".[dev]"
failpack demo --fast
```

Requires Python **3.11+**.

## What's new since 1.5.4

### Added

- GitHub Pages deploy workflow
  [`.github/workflows/pages.yml`](https://github.com/JiangSkirk/failpack/blob/v1.5.5/.github/workflows/pages.yml)
  — uploads `site/` and deploys with `actions/deploy-pages`.
- Expected homepage URL:
  [https://jiangskirk.github.io/failpack/](https://jiangskirk.github.io/failpack/)
  (GitHub Pages owner casing is lowercase). If the site is still dark after
  merge: **Settings → Pages → Build and deployment → Source: GitHub Actions**,
  then re-run the **Deploy GitHub Pages** workflow (or push a `site/` change).
- Site **Checkout (placeholder)** CTA under Pricing — disabled “coming soon”
  buttons; waitlist email until Creem KYC. **No fake pay links.**

### Changed

- [`site/index.html`](https://github.com/JiangSkirk/failpack/blob/v1.5.5/site/index.html)
  Quickstart shows `pip install failpack` (once on PyPI) **and** the git
  fallback, then `failpack demo --fast`. Privacy / Terms / waitlist kept.
- README dual-install story mirrors the site.
- README links the Pages landing; QUALITY_BAR homepage nice-to-have marked
  workflow-shipped (honest enable step if still pending).
- Version bump to **1.5.5**.
- Docs / walkthrough version samples → **1.5.5**.

## Verify locally

```bash
failpack --version          # failpack 1.5.5
failpack demo --fast
failpack list --json
failpack diff demo-five-minute
failpack lint
failpack replay --all
# both must stay green with demo leftover present:
pytest -q tests
(cd /tmp && pytest -q /path/to/failpack/tests)
```

Optional cleanup:

```bash
failpack rm demo-five-minute --force
```

## Action pin

Consumers should keep:

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.5.0
```

**Why not `@v1.5.5`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative.

## Non-goals for 1.5.5

- No **live** Creem checkout / KYC / pay links (placeholder CTA only)
- No PyPI upload without a token in env (`pip install failpack` documented as
  preferred once published; git fallback works today)
- No coupling to Echo, Orin, titan-agent, or any live agent install
- No Action pin retarget
- No invented “user” packs; unpaid stranger walkthrough still open

## Links

- Homepage (Pages): [https://jiangskirk.github.io/failpack/](https://jiangskirk.github.io/failpack/)
- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.5/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.5/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.5/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.5/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.5/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.5/CONTRIBUTING.md)
