# FailPack 1.3.0 — Release notes

Tag: `v1.3.0`.

## Highlights

FailPack **1.3.0** is the ~60-second stranger cut: `failpack demo --fast`,
Claude one-shot capture UX, watch FAIL STORY/`next:` tips, and PyPI-ready
packaging (upload only when you have a token).

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

## What's new since 1.2.0

### Added

- **`failpack demo --fast`** — ~60s stranger wow path (capture → promote →
  replay only; skips doctor dump / break / migrate).
- **Claude Code one-shot UX** — `capture --claude-latest` prints session path +
  `Next: promote --suggest …`; clearer not-found messages; doctor tip points at
  the one-shot (and `demo --fast`).
- **`failpack watch` FAIL surface** — same **STORY** block and **`next:`** tip as
  `failpack replay` on FAIL.
- README **Daily loop** section — capture → `promote --suggest` → replay → watch.
- **[`docs/PUBLISH.md`](https://github.com/JiangSkirk/failpack/blob/v1.3.0/docs/PUBLISH.md)** —
  exact TestPyPI / PyPI steps (upload only with token).
- PyPI-ready packaging: `LICENSE`, classifiers, project URLs, SPDX license.
- GitHub Release **`v1.2.0`** + [`RELEASE_NOTES_1.2.0.md`](https://github.com/JiangSkirk/failpack/blob/v1.3.0/RELEASE_NOTES_1.2.0.md).
- Action docs / examples / `init --ci` pin **`@v1.2.0`** (keep `@main` as
  alternative).

### Changed

- Version bump to **1.3.0**.
- Watch CLI header shows `PASS` / `FAIL` after capture → promote → replay.
- Docs timing: “Five-minute path” → “~60-second path”.

## Verify locally

```bash
failpack --version          # failpack 1.3.0
failpack doctor --score
failpack demo --fast
failpack lint
failpack replay --all
pytest -q
```

## Non-goals for 1.3.0

- No monetization / checkout / paid tiers in-tree
- No PyPI token publish in this release (packaging + docs only)
- No coupling to Echo, Orin, titan-agent, or any live agent install

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.3.0/CHANGELOG.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.3.0/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.3.0/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.3.0/CONTRIBUTING.md)
