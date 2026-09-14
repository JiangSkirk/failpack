# FailPack 1.1.0 — Release notes

Tag: `v1.1.0`.

## Highlights

FailPack **1.1.0** adds smarter promote suggestions and Cursor transcript capture,
plus a copy-paste stranger walkthrough.

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

## What's new since 1.0.0

### Added

- `failpack promote --suggest <id>` — analyze pack artifacts + transcript
  events and print recommended assertions (`exit_code`, fingerprint paths,
  `tool_denied_contains`, `bash_output_contains`). Add `--write` to apply.
  Plain `promote` / `re-promote` use the same smarter builder.
- `failpack capture --cursor-latest` — best-effort discovery of the newest
  Cursor agent `*.jsonl` under `~/.cursor/projects/*/agent-transcripts`
  (tests MUST use a fake HOME). Clear not-found message +
  [`examples/cursor-latest-demo.md`](https://github.com/JiangSkirk/failpack/blob/v1.1.0/examples/cursor-latest-demo.md).
- [`examples/STRANGER_WALKTHROUGH.md`](https://github.com/JiangSkirk/failpack/blob/v1.1.0/examples/STRANGER_WALKTHROUGH.md)
  — copy-paste install → demo → `doctor --score` session for new users.

### Changed

- Version bump to **1.1.0**.
- Promote writes smarter transcript-derived asserts when signals exist
  (still backward compatible for packs that omit them).
- Completion / help / README mention `--suggest`, `--write`, `--cursor-latest`.

## Verify locally

```bash
failpack --version          # failpack 1.1.0
failpack doctor --score
failpack demo --skip-break
failpack lint
failpack replay --all
pytest -q
```

## Non-goals for 1.1.0

- No monetization / checkout / paid tiers in-tree
- No PyPI token publish in this release
- No coupling to Echo, Orin, titan-agent, or any live agent install

## Links

- Changelog: [CHANGELOG.md](https://github.com/JiangSkirk/failpack/blob/v1.1.0/CHANGELOG.md)
- Pack index: [docs/PACKS.md](https://github.com/JiangSkirk/failpack/blob/v1.1.0/docs/PACKS.md)
- Stranger walkthrough: [examples/STRANGER_WALKTHROUGH.md](https://github.com/JiangSkirk/failpack/blob/v1.1.0/examples/STRANGER_WALKTHROUGH.md)
- Contributing: [CONTRIBUTING.md](https://github.com/JiangSkirk/failpack/blob/v1.1.0/CONTRIBUTING.md)
