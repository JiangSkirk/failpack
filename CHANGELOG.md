# Changelog

All notable changes to FailPack are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.3] — 2026-09-14

### Fixed

- Doctor / pack-count tests no longer assert exact `"4 pack"` / `"4 golden"`
  against the live REPO packs tree. They assert shipped fixture goldens by id
  and tolerate extra goldens left by `failpack demo --fast` (`demo-five-minute`),
  so the acceptance path `demo --fast` then `pytest` stays green.

### Changed

- Version bump to **1.5.3**.
- [`docs/QUALITY_BAR.md`](docs/QUALITY_BAR.md): smoke section notes demo may
  leave a pack; tests must not break because of it. Sell gaps still honest
  (PyPI / real-user packs / unpaid stranger walkthrough open).
- Docs / walkthrough version samples → **1.5.3**.

### Notes

- Quality-freeze thickening only. Action pin stays **`@v1.5.0`** (no Action
  behavior change). Demo happy-path still writes under `.failpack/` (stranger
  wow path unchanged).
- Zero coupling to Echo / Orin / titan-agent. No monetization. No PyPI upload
  without a token in env.

## [1.5.2] — 2026-09-14

### Added

- **[`docs/SUPPORT.md`](docs/SUPPORT.md)** — open support path: GitHub Issues +
  email `8725598a@gmail.com` (owner JiangSkirk). Linked from README and
  CONTRIBUTING. No Discord.
- GitHub Release **`v1.5.2`** + [`RELEASE_NOTES_1.5.2.md`](RELEASE_NOTES_1.5.2.md).

### Fixed

- Pytest hermeticity: `test_cli_list_prints_table` and `test_cli_show_json`
  pass `--root` to the repo checkout so `pytest -q tests` is green from any
  cwd (no ambient `.failpack` under `/tmp` / `/workspace`).

### Changed

- Version bump to **1.5.2**.
- Docs drift: CONTRIBUTING `--version` example **1.0.0 → 1.5.2**; stranger
  walkthrough sample output matches `demo --fast` (includes `Clean up with:`);
  readiness score note covers **90–92** when an empty Cursor projects dir
  earns half-credit; `five-minute-demo.sh` expects **1.5.x**.
- Doctor Cursor tips use `--id cursor-fail` (aligned with README).
- [`docs/QUALITY_BAR.md`](docs/QUALITY_BAR.md): Support path marked done; PyPI /
  real-user packs still honest (open).
- [`docs/LANDING.md`](docs/LANDING.md) Quickstart leads with `failpack demo --fast`
  (small stranger-doc sync with README / walkthrough).

### Notes

- Quality-freeze cut: support path, hermetic tests, landing sync, and the
  missing **`v1.5.2`** GitHub Release. Action pin stays **`@v1.5.0`** (no Action
  retarget — docs/examples/`init --ci` already pin the shipped Action at
  `v1.5.0`; this release does not change Action inputs/behavior).
- Zero coupling to Echo / Orin / titan-agent. No monetization. No PyPI upload
  without a token in env.

## [1.5.1] — 2026-09-14

### Added

- GitHub Release **`v1.5.0`** + [`RELEASE_NOTES_1.5.0.md`](RELEASE_NOTES_1.5.0.md).
- Action docs / examples / `init --ci` pin **`@v1.5.0`** (keep `@main` as
  alternative).

### Changed

- Version bump to **1.5.1**.

### Notes

- Docs-only pin bump after `v1.5.0` tagged. No features.
- Zero coupling to Echo / Orin / titan-agent. No monetization. No PyPI upload
  without a token in env.

## [1.5.0] — 2026-09-14

### Added

- GitHub Release **`v1.4.0`** + [`RELEASE_NOTES_1.4.0.md`](RELEASE_NOTES_1.4.0.md).
- Action docs / examples / `init --ci` pin **`@v1.4.0`** (keep `@main` as
  alternative).
- **[`docs/QUALITY_BAR.md`](docs/QUALITY_BAR.md)** — honest internal checklist of
  what “done enough to sell” still needs (PyPI token, real-user packs, …).

### Changed

- Version bump to **1.5.0**.
- README top pitch tightened to a ~30-second “why FailPack” (still leads with
  install → `demo --fast`; no hype adjectives).
- CLI clarity: `diff` FAIL **`next:`** tip order matches replay/explain
  (RESULT first); `diff` / `list` / `packs` help document exit codes; empty
  `list` prints a `demo --fast` / capture next tip.

### Notes

- Quality-freeze prep only — no big new features.
- Zero coupling to Echo / Orin / titan-agent. No monetization. No PyPI upload
  without a token in env.

## [1.4.0] — 2026-09-14

### Added

- **`failpack diff <id>`** — expected vs actual artifact summary **without** full
  assertion replay (short unified diffs; `--json` / `--no-diff`).
- **`failpack list --json`** / **`failpack packs --json`** — stable machine pack
  index (`id`, `status`, `exit_code`, `promoted_at`) for tooling.
- GitHub Release **`v1.3.0`** + [`RELEASE_NOTES_1.3.0.md`](RELEASE_NOTES_1.3.0.md).
- Action docs / examples / `init --ci` pin **`@v1.3.0`** (keep `@main` as
  alternative).

### Changed

- Version bump to **1.4.0**.
- Top-level help / install epilog lead with **`demo --fast`**.
- FAIL **`next:`** tips point at **`diff`** (replay/watch: `explain` · `diff` ·
  `re-promote`; explain: `diff` · `promote --suggest` · `re-promote`).
- Shell completion includes **`diff`**, **`packs`**, **`list --json`**, and
  **`demo --fast`**.

### Notes

- Stranger critique (clean venv install of `v1.3.0`): `demo --fast`,
  `doctor --score`, forced FAIL → `explain` — fixed help defaults and added
  `diff` so fingerprint drift does not require a second full replay.
- Zero coupling to Echo / Orin / titan-agent. No monetization. No PyPI upload
  without a token in env.

## [1.3.0] — 2026-09-14

### Added

- **`failpack demo --fast`** — ~60s stranger wow path (capture → promote →
  replay only; skips doctor dump / break / migrate). README + stranger
  walkthrough lead with this.
- **Claude Code one-shot UX** — `capture --claude-latest` prints session path +
  `Next: promote --suggest …`; clearer not-found messages; doctor tip points at
  the one-shot (and `demo --fast`).
- **`failpack watch` FAIL surface** — same **STORY** block and **`next:`** tip as
  `failpack replay` on FAIL (`explain` · `promote --suggest` · `re-promote`).
- README **Daily loop** section — capture → `promote --suggest` → replay → watch.
- **[`docs/PUBLISH.md`](docs/PUBLISH.md)** — exact TestPyPI / PyPI steps
  (`python -m build`, `twine check`, upload only with token).
- PyPI-ready packaging: `LICENSE`, classifiers, project URLs, SPDX license,
  trimmed sdist includes (no publish without token).
- GitHub Release **`v1.2.0`** + [`RELEASE_NOTES_1.2.0.md`](RELEASE_NOTES_1.2.0.md).
- Action docs / examples / `init --ci` pin **`@v1.2.0`** (keep `@main` as
  alternative).

### Changed

- Version bump to **1.3.0**.
- Watch CLI header shows `PASS` / `FAIL` after capture → promote → replay.
- Docs timing: “Five-minute path” → “~60-second path”; Claude demo + stranger
  walkthrough polished for one-shot capture.

### Notes

- Zero coupling to Echo / Orin / titan-agent. No monetization. No PyPI upload
  in this release (packaging + docs only).

## [1.2.0] — 2026-09-14

### Added

- **`failpack doctor --score` soft `cursor_projects` check** — same spirit as
  Claude: optional `~/.cursor/projects` row (+5 pts). Missing Cursor/Claude
  does **not** break CI (fixtures / `failpack demo` still reach **90/100**).
- Replay / explain **`next:`** tip on FAIL — one-line FAIL→FIX loop:
  `explain` · `promote --suggest` · `re-promote`.
- GitHub Release **`v1.1.0`** + [`RELEASE_NOTES_1.1.0.md`](RELEASE_NOTES_1.1.0.md).
- Action docs / examples / `init --ci` pin **`@v1.1.0`** (keep `@main` as
  alternative).

### Changed

- Version bump to **1.2.0**.
- Soft agent score split: `claude_projects` **5** + `cursor_projects` **5**
  (was Claude-only 10).
- [`examples/STRANGER_WALKTHROUGH.md`](examples/STRANGER_WALKTHROUGH.md) —
  clean-temp-dir realism (0 packs before capture; `promote --suggest
  demo-five-minute`; PATH tip; Cursor score row; `next:` tip).

### Notes

- Zero coupling to Echo / Orin / titan-agent. No monetization / PyPI publish.

## [1.1.0] — 2026-09-14

### Added

- **`failpack promote --suggest <id>`** — analyze pack artifacts + transcript
  events (ticks) and print recommended assertions (`exit_code`, fingerprint
  paths, `tool_denied_contains`, `bash_output_contains`). Add **`--write`** to
  apply. Plain `promote` / `re-promote` use the same smarter builder.
- **`failpack capture --cursor-latest`** — best-effort discovery of the newest
  Cursor agent `*.jsonl` under `~/.cursor/projects/*/agent-transcripts`
  (tests MUST use a fake HOME). Clear not-found message +
  [`examples/cursor-latest-demo.md`](examples/cursor-latest-demo.md).
- **[`examples/STRANGER_WALKTHROUGH.md`](examples/STRANGER_WALKTHROUGH.md)** —
  copy-paste install → demo → `doctor --score` session for new users.
- GitHub Release **`v1.0.0`** from [`RELEASE_NOTES_1.0.0.md`](RELEASE_NOTES_1.0.0.md).

### Changed

- Version bump to **1.1.0**.
- Promote writes smarter transcript-derived asserts when signals exist
  (still backward compatible for packs that omit them).
- Completion / help / README mention `--suggest`, `--write`, `--cursor-latest`.

### Notes

- Zero coupling to Echo / Orin / titan-agent. No monetization / PyPI publish.
- Cursor discovery is best-effort; layouts evolve — see the example doc.

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
