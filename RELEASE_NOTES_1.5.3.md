# FailPack 1.5.3 — Release notes

Tag: `v1.5.3`.

## Highlights

FailPack **1.5.3** is a small **quality-freeze** cut: doctor / pack-count tests
no longer hardcode a fragile exact inventory of **4** packs, so the acceptance
path `failpack demo --fast` then `pytest` stays green when the demo leaves
`demo-five-minute` under `.failpack/packs/`. Action pin stays **`@v1.5.0`**.

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

## What's new since 1.5.2

### Fixed

- Doctor tests assert shipped fixture goldens **by id** (and `>= N` golden
  count) instead of exact `"4 pack"` / `"4 golden"` against the live REPO
  packs tree. Running `demo --fast` in a checkout before pytest no longer
  fails `test_doctor_ok_on_repo` / `test_doctor_score_on_repo`.

### Changed

- Version bump to **1.5.3**.
- [`docs/QUALITY_BAR.md`](https://github.com/JiangSkirk/failpack/blob/v1.5.3/docs/QUALITY_BAR.md)
  smoke note: demo may leave a pack; tests must tolerate it.
- Docs / walkthrough version samples → **1.5.3**.

## Verify locally

```bash
failpack --version          # failpack 1.5.3
failpack doctor --score
failpack demo --fast        # may leave .failpack/packs/demo-five-minute
failpack list --json
failpack diff demo-five-minute
failpack lint
failpack replay --all
# both must stay green with demo leftover present:
pytest -q tests
(cd /tmp && pytest -q /path/to/failpack/tests)
```

Removing the leftover demo pack is optional cleanup, not required for green
tests:

```bash
failpack rm demo-five-minute --force
```

## Action pin

Consumers should keep:

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.5.0
```

**Why not `@v1.5.3`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative.

## Non-goals for 1.5.3

- No monetization / checkout / paid tiers in-tree
- No PyPI upload without a token in env
- No coupling to Echo, Orin, titan-agent, or any live agent install
- No Action pin retarget
- No invented “user” packs; unpaid stranger walkthrough still open
- Demo happy-path UX unchanged (still writes under `.failpack/` by design)

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.3/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.3/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.3/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.3/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.3/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.3/CONTRIBUTING.md)
