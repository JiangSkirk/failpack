# FailPack 1.5.2 — Release notes

Tag: `v1.5.2`.

## Highlights

FailPack **1.5.2** is a **quality-freeze** cut: open support path, hermetic
pytest from any cwd, landing Quickstart synced to `demo --fast`, and this
GitHub Release (package version was already 1.5.2; Release lagged at v1.5.0).
No big new features. Action pin stays **`@v1.5.0`**.

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

## What's new since 1.5.0

### Added

- **[`docs/SUPPORT.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.2/docs/SUPPORT.md)** —
  GitHub Issues + email `8725598a@gmail.com` (owner JiangSkirk). Linked from
  README and CONTRIBUTING. No Discord.
- GitHub Release **`v1.5.2`** + this file.
- Intermediate **1.5.1** pin bump after `v1.5.0` (Action docs / examples /
  `init --ci` → `@v1.5.0`).

### Fixed

- Pytest hermeticity: CLI `list` / `show --json` tests pass `--root` so
  `pytest -q tests` is green from a dirty cwd (no ambient pack root under
  `/tmp` or `/workspace`).

### Changed

- Version bump to **1.5.2**.
- Docs drift: CONTRIBUTING `--version` example, stranger walkthrough sample
  output, readiness score notes, `five-minute-demo.sh` expects **1.5.x**.
- Doctor Cursor tips use `--id cursor-fail` (aligned with README).
- [`docs/QUALITY_BAR.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.2/docs/QUALITY_BAR.md):
  Support path marked done; PyPI / real-user packs still honest (open).
- [`docs/LANDING.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.2/docs/LANDING.md)
  Quickstart leads with `failpack demo --fast`.

## Verify locally

```bash
failpack --version          # failpack 1.5.2
failpack doctor --score
failpack demo --fast
failpack list --json
failpack diff demo-five-minute
failpack lint
failpack replay --all
# hermetic: green from any cwd
(cd /tmp && pytest -q /path/to/failpack/tests)
```

## Action pin

Consumers should keep:

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.5.0
```

**Why not `@v1.5.2`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin; retargeting would force every consumer
workflow rewrite for docs-only + test hermeticity. `@main` remains a valid
tip alternative.

## Non-goals for 1.5.2

- No monetization / checkout / paid tiers in-tree
- No PyPI upload without a token in env
- No coupling to Echo, Orin, titan-agent, or any live agent install
- No big new features (quality-freeze only)
- No Action pin retarget

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.2/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.2/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.2/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.2/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.2/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.2/CONTRIBUTING.md)
