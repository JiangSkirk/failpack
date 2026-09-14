# FailPack 1.5.6 — Release notes

Tag: `v1.5.6`.

## Highlights

FailPack **1.5.6** is a small **quality-freeze honesty** cut: docs and the
static site now lead with the **live PyPI** install path (first upload was
**1.5.5**). Git install is fallback only. Action pin stays **`@v1.5.0`**.
**No PyPI re-upload from this release.**

## Install

```bash
pip install failpack
failpack demo --fast
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
```

Requires Python **3.11+**.

## What's new since 1.5.5

### Changed

- README / [`site/index.html`](https://github.com/JiangSkirk/failpack/blob/v1.5.6/site/index.html)
  / [`docs/LANDING.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.6/docs/LANDING.md)
  Quickstart lead with `pip install failpack` + `failpack demo --fast`.
- [`docs/QUALITY_BAR.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.6/docs/QUALITY_BAR.md):
  **PyPI token + first upload** marked **done** (1.5.5). Pages note tightened
  to a one-time Settings → Pages → Source: **GitHub Actions** flip if the site
  is still dark. Expected URL:
  [https://jiangskirk.github.io/failpack/](https://jiangskirk.github.io/failpack/).
- [`docs/PUBLISH.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.6/docs/PUBLISH.md):
  post-publish status (live since 1.5.5; do not re-upload without a token /
  new version).
- Stranger walkthrough + CLI help tip PyPI first.
- Version bump to **1.5.6**.
- Docs / walkthrough version samples → **1.5.6**.

## Verify locally

```bash
failpack --version          # failpack 1.5.6
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

**Why not `@v1.5.6`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative.

## Non-goals for 1.5.6

- No **live** Creem checkout / KYC / pay links (placeholder CTA only)
- No PyPI re-upload (1.5.5 already live; this cut is docs/honesty only)
- No coupling to Echo, Orin, titan-agent, or any live agent install
- No Action pin retarget
- No invented “user” packs; unpaid stranger walkthrough still open
- Pages enable remains a human one-time Settings flip if still 404

## Links

- Homepage (Pages): [https://jiangskirk.github.io/failpack/](https://jiangskirk.github.io/failpack/)
- PyPI: [https://pypi.org/project/failpack/](https://pypi.org/project/failpack/)
- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.6/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.6/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.6/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.6/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.6/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.6/CONTRIBUTING.md)
