# FailPack 1.5.10 — Release notes

Tag: `v1.5.10`.

## Highlights

FailPack **1.5.10** is a small stranger-friction cut on **doctor** behavior after
1.5.9’s pip-installable Cursor hermetic demo. Two accept-script pains from
1.5.8/1.5.9:

1. **Ancestor `.failpack` pollution** — `failpack doctor` under an empty
   subdirectory no longer climbs to a parent `.failpack/` and scores “already
   set up”. Doctor scores **cwd** (or explicit `--root`) only.
2. **Machineable exit** — `RESULT: NEEDS SETUP` now exits **1** (OK stays **0**).
   `--score` text is unchanged; `--strict` remains as a compatibility alias.

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
failpack doctor --score   # empty cwd → NEEDS SETUP, exit 1
failpack demo --fast
failpack demo --claude-hermetic
failpack demo --cursor-hermetic
```

Requires Python **3.11+**.

## What's new since 1.5.9

### Changed

- **Doctor project root** — scores cwd / `--root` only; does **not** silently
  inherit ancestor `.failpack/` packs (other commands still climb via
  `find_root`).
- **Doctor exit codes** — `RESULT: OK` → exit **0**; `NEEDS SETUP` / `FAIL` →
  exit **1**. `--strict` kept for compatibility (same rules).
- When readiness score is **≥90**, soft Claude/Cursor “set up agent” tips are
  muted so post-demo doctor output does not dominate as “you must set up Cursor”.
- Version bump to **1.5.10**.
- Docs / walkthrough / site version samples → **1.5.10**.

### Added

- GitHub Release **`v1.5.10`** + this file.
- Tests: empty nested cwd without local `.failpack` → NEEDS SETUP (no ancestor
  inheritance); NEEDS SETUP → non-zero CLI exit.

## Verify locally

```bash
failpack --version          # failpack 1.5.10
# empty dir (optional):
#   mkdir -p /tmp/fp-empty && cd /tmp/fp-empty
#   failpack doctor --score   # NEEDS SETUP, exit 1
failpack demo --fast
failpack demo --claude-hermetic
failpack demo --cursor-hermetic
failpack list --json
failpack lint
failpack replay --all
# must stay green with demo leftovers present:
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

**Why not `@v1.5.10`?** This release does not change Action inputs or behavior.
`v1.5.0` remains the shipped Action pin. `@main` remains a valid tip
alternative. (Projects that already have packs still get doctor RESULT: OK /
exit 0.)

## Non-goals for 1.5.10

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
- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.5.10/CHANGELOG.md)
- Support: [docs/SUPPORT.md](https://github.com/JiangSkirk/failpack/blob/v1.5.10/docs/SUPPORT.md)
- Quality bar: [docs/QUALITY_BAR.md](https://github.com/JiangSkirk/failpack/blob/v1.5.10/docs/QUALITY_BAR.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.5.10/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.5.10/examples/STRANGER_WALKTHROUGH.md)
- Hermetic Claude CLI: `failpack demo --claude-hermetic`
- Hermetic Cursor CLI: `failpack demo --cursor-hermetic`
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.5.10/CONTRIBUTING.md)
