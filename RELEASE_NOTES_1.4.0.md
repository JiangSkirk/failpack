# FailPack 1.4.0 — Release notes

Tag: `v1.4.0`.

## Highlights

FailPack **1.4.0** adds **`failpack diff`** (expected vs actual without a full
replay) and **`list --json` / `packs --json`**, plus help / FAIL-tip polish from
a clean-venv stranger critique of `demo --fast`.

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

## What's new since 1.3.0

### Added

- **`failpack diff <id>`** — expected vs actual artifact summary **without**
  full assertion replay (short unified diffs; `--json` / `--no-diff`).
- **`failpack list --json`** / **`failpack packs --json`** — stable machine pack
  index (`id`, `status`, `exit_code`, `promoted_at`) for tooling.
- GitHub Release **`v1.3.0`** + [`RELEASE_NOTES_1.3.0.md`](https://github.com/JiangSkirk/failpack/blob/v1.4.0/RELEASE_NOTES_1.3.0.md).
- Action docs / examples / `init --ci` pin **`@v1.3.0`** (keep `@main` as
  alternative).

### Changed

- Version bump to **1.4.0**.
- Top-level help / install epilog lead with **`demo --fast`**.
- FAIL **`next:`** tips point at **`diff`** (replay/watch: `explain` · `diff` ·
  `re-promote`; explain: `diff` · `promote --suggest` · `re-promote`).
- Shell completion includes **`diff`**, **`packs`**, **`list --json`**, and
  **`demo --fast`**.

## Verify locally

```bash
failpack --version          # failpack 1.4.0
failpack doctor --score
failpack demo --fast
failpack list --json
failpack diff demo-five-minute
failpack lint
failpack replay --all
pytest -q
```

## Non-goals for 1.4.0

- No monetization / checkout / paid tiers in-tree
- No PyPI token publish in this release (packaging + docs only)
- No coupling to Echo, Orin, titan-agent, or any live agent install

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.4.0/CHANGELOG.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.4.0/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.4.0/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.4.0/CONTRIBUTING.md)
