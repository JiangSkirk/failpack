# FailPack 1.2.0 — Release notes

Tag: `v1.2.0`.

## Highlights

FailPack **1.2.0** kills stranger friction: soft Cursor doctor scoring, a
one-line FAIL→FIX `next:` tip on replay/explain, and a realistic stranger
walkthrough.

## Install

```bash
pip install "git+https://github.com/JiangSkirk/failpack.git"
failpack demo
```

Editable / local:

```bash
git clone https://github.com/JiangSkirk/failpack.git
cd failpack
pip install -e ".[dev]"
failpack demo
```

Requires Python **3.11+**.

## What's new since 1.1.0

### Added

- `failpack doctor --score` soft `cursor_projects` check — optional
  `~/.cursor/projects` row (+5 pts). Missing Cursor/Claude does **not**
  break CI (fixtures / `failpack demo` still reach **90/100**).
- Replay / explain **`next:`** tip on FAIL — one-line FAIL→FIX loop:
  `explain` · `promote --suggest` · `re-promote`.
- GitHub Release **`v1.1.0`** + [`RELEASE_NOTES_1.1.0.md`](https://github.com/JiangSkirk/failpack/blob/v1.1.0/RELEASE_NOTES_1.1.0.md).
- Action docs / examples / `init --ci` pin **`@v1.1.0`** (keep `@main` as
  alternative).

### Changed

- Version bump to **1.2.0**.
- Soft agent score split: `claude_projects` **5** + `cursor_projects` **5**
  (was Claude-only 10).
- [`examples/STRANGER_WALKTHROUGH.md`](https://github.com/JiangSkirk/failpack/blob/v1.2.0/examples/STRANGER_WALKTHROUGH.md)
  — clean-temp-dir realism (0 packs before capture; `promote --suggest
  demo-five-minute`; PATH tip; Cursor score row; `next:` tip).

## Verify locally

```bash
failpack --version          # failpack 1.2.0
failpack doctor --score
failpack demo --skip-break
failpack lint
failpack replay --all
pytest -q
```

## Non-goals for 1.2.0

- No monetization / checkout / paid tiers in-tree
- No PyPI token publish in this release
- No coupling to Echo, Orin, titan-agent, or any live agent install

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.2.0/CHANGELOG.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.2.0/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.2.0/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.2.0/CONTRIBUTING.md)
