# FailPack 1.0.0 — Release notes (draft)

Paste into a GitHub Release when ready. Tag suggestion: `v1.0.0`.

## Highlights

FailPack **1.0.0** is the stranger-ready cut: install from git without PyPI, run
`failpack demo` first, and check readiness with `failpack doctor --score`.

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

## What's new since 0.9.0

### Added

- `failpack doctor --score` — **0–100 readiness score** + checklist:
  - python
  - packs_dir
  - claude_projects
  - lint
  - golden_count
- `failpack doctor --strict` — non-zero exit when doctor checks FAIL
- `RELEASE_NOTES_1.0.0.md` (this file)
- README version badge

### Changed

- Primary install is the **git+https** one-liner (no PyPI token / publish required)
- `failpack demo` is the documented first command after install
- `failpack doctor` is **advisory** (exit 0) unless `--strict`
- Composite Action runs `failpack doctor --score`
- Clearer capture errors when no transcript source is given

### Unchanged (kept from 0.9)

- `failpack demo`, `explain`, `lint`, `report`, `show`, `export`/`import`,
  `replay --all`, `promote --dry-run`, `rm`/`rename`, `completion`, `migrate`, …
- Four shipped goldens + `failpack demo` wow path
- Reusable Action: `JiangSkirk/failpack/.github/actions/failpack-replay@v1.0.0`
  (or `@main`)

## Verify locally

```bash
failpack --version          # failpack 1.0.0
failpack doctor --score
failpack demo --skip-break
failpack lint
failpack replay --all
pytest -q
```

## Non-goals for 1.0.0

- No monetization / checkout / paid tiers in-tree
- No PyPI token publish in this release
- No coupling to Echo, Orin, titan-agent, or any live agent install

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/main/CHANGELOG.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/main/docs/PACKS.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/main/CONTRIBUTING.md)
