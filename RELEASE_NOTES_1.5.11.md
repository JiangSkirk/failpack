# FailPack 1.5.11 — Release notes

Tag: `v1.5.11`.

## Highlights

FailPack **1.5.11** finishes the stranger-friction cut started in **1.5.10**.
Doctor already scored cwd only (no ancestor inherit). Remaining accept pain:
`failpack demo --fast` / hermetic demos / first-time capture still climbed via
`find_root` and wrote packs into a **parent** `.failpack/` when cwd was a nested
empty directory. Demo said PASS; doctor in that cwd said NEEDS SETUP.

**1.5.11** makes the wow path cwd-local: demo / init / first-time capture write
under cwd (or `--root`), not an ancestor layout. After demo, doctor in the same
cwd becomes OK. List / replay / promote of an already-discovered project still
climb via `find_root`.

Action pin stays **`@v1.5.0`**. **No PyPI upload from this agent.**

## Install

```bash
pip install failpack
failpack demo --fast
failpack demo --claude-hermetic
failpack demo --cursor-hermetic
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
# nested empty under a parent with .failpack/:
#   mkdir -p /tmp/parent/accept && mkdir -p /tmp/parent/.failpack/packs
#   cd /tmp/parent/accept
#   failpack demo --fast          # creates ./ .failpack/ locally
#   failpack doctor --score       # RESULT: OK (agrees with demo)
failpack --version                # failpack 1.5.11
```

Requires Python **3.11+**.

## What's new since 1.5.10

### Changed

- **`local_root`** — shared cwd / `--root` helper (no ancestor climb). Used by
  doctor, demo, init, and capture writes.
- **Demo / init / capture** — prefer local layout; do **not** silently write
  into an ancestor `.failpack/` when cwd has none.
- Doctor behavior from 1.5.10 unchanged: no ancestor inherit for scoring;
  NEEDS SETUP / FAIL → exit 1; OK → 0.
- Version bump to **1.5.11**.
- Docs / walkthrough / site version samples → **1.5.11**.

### Added

- GitHub Release **`v1.5.11`** + this file.
- Tests: nested empty cwd under parent with `.failpack/` → `demo --fast`
  creates local packs; doctor OK after demo; ancestor packs unchanged; capture
  without local layout does not climb.

## Verify locally

```bash
failpack --version          # failpack 1.5.11
failpack doctor --score
failpack demo --fast
failpack demo --claude-hermetic
failpack demo --cursor-hermetic
failpack list --json
failpack lint
failpack replay --all
pytest -q tests
(cd /tmp && pytest -q /path/to/failpack/tests)
```

Optional cleanup:

```bash
failpack rm demo-five-minute --force
failpack rm claude-hermetic --force
failpack rm cursor-hermetic --force
```

## Action pin

Consumers should keep:

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.5.0
```

**Why not `@v1.5.11`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative.

## Non-goals for 1.5.11

- No **live** Creem checkout / KYC / pay links (placeholder CTA only)
- No PyPI upload from this agent (1.5.5+ already live; human-held token for
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
- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.11/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.11/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.11/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.11/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.11/examples/STRANGER_WALKTHROUGH.md)
- Hermetic Claude CLI: `failpack demo --claude-hermetic`
- Hermetic Cursor CLI: `failpack demo --cursor-hermetic`
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.11/CONTRIBUTING.md)
