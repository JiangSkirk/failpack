# FailPack 1.5.4 — Release notes

Tag: `v1.5.4`.

## Highlights

FailPack **1.5.4** is a small **quality-freeze** cut from a clean-venv stranger
critique of `v1.5.3`: demo cleanup teaches `failpack rm … --force` (not
`rm -rf`), and empty-project `doctor --score` leads with `demo --fast` /
`init` instead of a scary FAIL-only footer. Action pin stays **`@v1.5.0`**.

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

## What's new since 1.5.3

### Fixed

- Demo footer cleanup tip: `failpack rm <id> --force` (was absolute-path
  `rm -rf …/demo-five-minute`, which bypasses the CLI).
- Empty-root doctor: layout / packs_dir tips lead with
  `failpack demo --fast` (or `failpack init`). When the only hard miss is
  never-initialized layout, RESULT is **NEEDS SETUP** with a `next:` tip
  (layout still not OK; `--strict` still exits 1).

### Changed

- Version bump to **1.5.4**.
- [`docs/QUALITY_BAR.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.4/docs/QUALITY_BAR.md)
  status → **1.5.4**.
- Docs / walkthrough version samples → **1.5.4**; stranger cleanup sample
  synced to `failpack rm … --force`.

## Verify locally

```bash
failpack --version          # failpack 1.5.4
# empty dir (optional): failpack doctor --score  → NEEDS SETUP + next: demo --fast
failpack demo --fast        # cleanup tip: failpack rm demo-five-minute --force
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

**Why not `@v1.5.4`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative.

## Non-goals for 1.5.4

- No monetization / checkout / paid tiers in-tree
- No PyPI upload without a token in env
- No coupling to Echo, Orin, titan-agent, or any live agent install
- No Action pin retarget
- No invented “user” packs; unpaid stranger walkthrough still open

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.4/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.4/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.4/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.4/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.4/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.4/CONTRIBUTING.md)
