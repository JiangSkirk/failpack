# FailPack 1.5.0 — Release notes

Tag: `v1.5.0`.

## Highlights

FailPack **1.5.0** is a **quality-freeze prep** cut: tighter README pitch, clearer
CLI exit-code / empty-list help, and an honest [`docs/QUALITY_BAR.md`](docs/QUALITY_BAR.md)
checklist of what “done enough to sell” still needs. No big new features.

## Install

```bash
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

## What's new since 1.4.0

### Added

- GitHub Release **`v1.4.0`** + [`RELEASE_NOTES_1.4.0.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.0/RELEASE_NOTES_1.4.0.md).
- Action docs / examples / `init --ci` pin **`@v1.4.0`** (keep `@main` as
  alternative).
- **[`docs/QUALITY_BAR.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.0/docs/QUALITY_BAR.md)** —
  honest internal checklist of what “done enough to sell” still needs (PyPI
  token, real-user packs, …).

### Changed

- Version bump to **1.5.0**.
- README top pitch tightened to a ~30-second “why FailPack” (still leads with
  install → `demo --fast`; no hype adjectives).
- CLI clarity: `diff` FAIL **`next:`** tip order matches replay/explain
  (RESULT first); `diff` / `list` / `packs` help document exit codes; empty
  `list` prints a `demo --fast` / capture next tip.

## Verify locally

```bash
failpack --version          # failpack 1.5.0
failpack doctor --score
failpack demo --fast
failpack list --json
failpack diff demo-five-minute
failpack lint
failpack replay --all
pytest -q
```

## Non-goals for 1.5.0

- No monetization / checkout / paid tiers in-tree
- No PyPI upload without a token in env
- No coupling to Echo, Orin, titan-agent, or any live agent install
- No big new features (quality-freeze prep only)

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.0/CHANGELOG.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.0/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.0/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.0/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.0/CONTRIBUTING.md)
