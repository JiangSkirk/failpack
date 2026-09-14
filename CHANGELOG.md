# Changelog

All notable changes to FailPack are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-09-14

### Added

- **`failpack doctor --score`** — prints a **0–100 readiness score** plus checklist
  (python, packs_dir, claude_projects, lint, golden_count).
- **`failpack doctor --strict`** — exit non-zero when any doctor check FAILs.
- **`RELEASE_NOTES_1.0.0.md`** — maintainer-pasteable GitHub Release draft.
- Version badge on README.

### Changed

- Version bump to **1.0.0** (stranger-ready “1.0 feel”).
- **Install story:** primary one-liner is
  `pip install "git+https://github.com/JiangSkirk/failpack.git"` (no PyPI required);
  **`failpack demo`** is the first command after install.
- **`failpack doctor`** exits **0** by default (advisory); use `--strict` to gate.
- Composite action runs `failpack doctor --score`.
- Capture with no args prints a short tip list (`demo` / `--claude-latest` / path / stdin).
- Help / examples / CONTRIBUTING / landing copy use the git install URL.

### Notes

- All prior 0.9 commands remain (`demo`, `explain`, `lint`, `report`, `replay --all`, …).
- Zero coupling to Echo / Orin / titan-agent. No monetization / PyPI publish in this cut.

## [0.9.0] — 2026-09-14

### Added

- **`failpack explain [id]`** — short coherent FAIL story (what broke / which
  assertion / what to do next). Omit *id* to explain every currently failing
  golden pack.
- Replay **STORY** block on FAIL (single pack and `replay --all`); report
  markdown and `--json` include the same narrative.
- **`docs/PACKS.md`** — index of the four shipped goldens + `failpack demo`
  path, with failure class each teaches.
- README **five-minute path** polish + copy-pasteable Action / step-summary
  snippet (`run-lint` / `step-summary` defaults documented).

### Changed

- Version bump to **0.9.0**.
- `examples/five-minute-demo.sh` expects **0.9.x**.
- Completion scripts list `explain`.

### Notes

- Zero coupling to Echo / Orin / titan-agent (or any live agent install).
- No monetization in this release — open CLI stays the product.

## [0.8.0] — 2026-09-14

### Added

- **`failpack rm <id> [--force]`** — delete a pack directory; refuses without
  `--force` when status is `golden`.
- **`failpack rename <old> <new>`** — rename pack id, directory, `meta.id`, and
  `assertions.yaml` `pack_id`.
- **`failpack promote --dry-run <id>`** (also `promote <id> --dry-run`) — print
  the assertions YAML that would be written without writing; existing promote
  behavior unchanged. Same flag on `re-promote`.
- **Assertion schema validate** on promote / replay load (`read_assertions` /
  `write_assertions`): clear `ValueError` for unknown assertion kinds or missing
  required fields (no silent ignore).
- **`failpack lint [id]`** — light pack validate (layout + assertion schema;
  exit non-zero on errors).
- **`failpack report [id]`** — markdown replay summary for CI; `--github`
  appends to `$GITHUB_STEP_SUMMARY`. Composite action writes a step summary
  and runs `lint` by default.
- **`failpack completion bash|zsh`** — print an installable shell completion
  script (argparse-style; pack ids from `failpack list`).
- README **Pack lifecycle** section.

### Changed

- Version bump to **0.8.0**.
- `examples/five-minute-demo.sh` expects **0.8.x**.
- Composite action: optional `run-lint` / `step-summary` inputs (both default on).

### Notes

- Zero coupling to Echo / Orin / titan-agent (or any live agent install).
- No monetization in this release — open CLI stays the product.

## [0.7.0] — 2026-09-14

### Added

- **`failpack show <id>`** — pretty inspect one pack (status, exit, promoted_at,
  assertion summary, artifact list). Supports `--json`.
- New assertion kinds (documented + tested; older packs unchanged):
  - **`tool_denied_contains`** — transcript/tool events mention a denied tool name
    substring
  - **`bash_output_contains`** — last/any Bash tool output contains a string
    (`match: any|last`)
- Fourth golden pack: **`demo-tool-denied`** (fixture-based; uses the new asserts).
- Action docs: [`.github/actions/failpack-replay/README.md`](.github/actions/failpack-replay/README.md)
  with inputs / exit-code signal / examples.
- `failpack init` workspace tip README points to `failpack demo` and
  `capture --claude-latest`.
- README CI status badge.

### Changed

- Version bump to **0.7.0**.
- `examples/five-minute-demo.sh` expects **0.7.x** (still works; prefer `failpack demo`).

### Notes

- Zero coupling to Echo / Orin / titan-agent (or any live agent install).
- No monetization in this release — open CLI stays the product.

## [0.6.0] — 2026-09-14

### Added

- **`failpack export <id> [-o pack.tgz]`** — share a golden pack as `.tgz` / `.tar.gz` /
  `.zip` (assertions + expected + meta + artifacts + transcript + manifest).
- **`failpack import <pack.tgz>`** — restore into `.failpack/packs/` with id collision
  handling (`--force` overwrite, `--rename <id>`).
- **`failpack demo`** — one-command five-minute wow path (bundled fixture) so
  `pip install failpack && failpack demo` works without a git checkout.
- **`doctor`** reports whether `~/.claude/projects` exists and how many session
  `*.jsonl` files are present; tips `capture --claude-latest` when found.
- README front matter: ≤3-command real-session happy path + `failpack demo`.

### Changed

- Version bump to **0.6.0**.
- `examples/five-minute-demo.sh` expects **0.6.x** (still works; prefer `failpack demo`).

### Notes

- Zero coupling to Echo / Orin / titan-agent (or any live agent install).
- No monetization in this release — open CLI stays the product.

## [0.5.0] — 2026-09-14

### Added

- **`failpack capture --claude-latest`** — discover the newest Claude Code session
  JSONL under `~/.claude/projects` (magic capture path). Tests use a fake `HOME`
  fixture and never require a real `~/.claude` tree.
- **`failpack re-promote <id>`** — refresh `assertions.yaml` + `expected/` snapshots
  from current pack artifacts after an intentional fix / accepted drift.
- Clean, progress-free aligned **table** output for `failpack list`.
- End-of-run **SUMMARY** for `failpack replay --all` (passed/failed counts + failed
  pack ids, with a re-promote tip).
- [`examples/claude-latest-demo.md`](examples/claude-latest-demo.md) — walkthrough of
  the `--claude-latest` flow with screenshots-as-text.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to develop and test FailPack.

### Changed

- Version bump to **0.5.0**.
- README documents magic capture, re-promote, and TTY table / summary polish.
- `examples/five-minute-demo.sh` expects **0.5.x**.

### Notes

- Zero coupling to Echo / Orin / titan-agent (or any live agent install).
- No monetization in this release — open CLI stays the product.

## [0.4.0] — 2026-09-14

### Added

- Diff-aware explain on fingerprint FAIL (promote-time `expected/` snapshots).
- `failpack watch` — capture → promote → replay helper.
- `failpack migrate` — stamp `schema_version`.
- `failpack init --ci` — write starter GitHub Actions workflow.
- Composite action under `.github/actions/failpack-replay`.

## [0.3.0] — 2026-09-14

### Added

- Explainable replay (expected / actual / hint).
- Third golden pack: `demo-permission-denied`.
- Reusable composite Action for other repos.

## [0.2.0] — 2026-09-14

### Added

- `failpack doctor`.
- `failpack replay --all`.
- Smoother install / capture (directory newest-jsonl, `--from-claude-project`,
  `--stdin`, `--glob`).

## [0.1.0] — 2026-09-14

### Added

- Initial `init` / `capture` / `promote` / `replay` loop.
- Demo golden pack `demo-missing-import`.
- Fixture-based Claude-Code-like JSONL parsing.

[0.7.0]: https://github.com/JiangSkirk/failpack/releases/tag/v0.7.0
[0.6.0]: https://github.com/JiangSkirk/failpack/releases/tag/v0.6.0
[0.5.0]: https://github.com/JiangSkirk/failpack/releases/tag/v0.5.0
[0.4.0]: https://github.com/JiangSkirk/failpack/releases/tag/v0.4.0
[0.3.0]: https://github.com/JiangSkirk/failpack/releases/tag/v0.3.0
[0.2.0]: https://github.com/JiangSkirk/failpack/releases/tag/v0.2.0
[0.1.0]: https://github.com/JiangSkirk/failpack/releases/tag/v0.1.0
