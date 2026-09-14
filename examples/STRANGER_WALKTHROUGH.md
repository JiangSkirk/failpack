# Stranger walkthrough — FailPack from zero (~60s)

Copy-paste terminal session a new user would see: `pip install failpack` →
`failpack demo --fast` → hermetic Claude / Cursor demos → optional real
one-shot. No Echo / Orin / titan-agent. Git install is fallback only.

Assumes Python **3.11+** and a clean shell (empty project dir — not the FailPack
repo checkout). Target: **about a minute** to first PASS after install.

## 1) Install from PyPI

```bash
$ pip install failpack
Collecting failpack
  …
Successfully installed failpack-1.5.11 …

$ failpack --version
failpack 1.5.11
```

Git fallback (optional):

```bash
$ pip install "git+https://github.com/JiangSkirk/failpack.git"
```

Editable checkout (optional, for contributing):

```bash
$ git clone https://github.com/JiangSkirk/failpack.git
$ cd failpack
$ pip install -e ".[dev]"
$ failpack --version
failpack 1.5.11
```

> Tip: if `failpack: command not found`, add your user scripts dir to `PATH`
> (often `~/.local/bin` after `pip install --user`).

## 2) First wow — `failpack demo --fast` (~60s)

From an **empty** project directory (or any repo without packs yet):

```bash
$ mkdir /tmp/failpack-try && cd /tmp/failpack-try
$ failpack demo --fast
failpack demo --fast  (~60s wow)  ·  failpack 1.5.11

==> 1/3  capture bundled fixture → 'demo-five-minute'
Captured pack 'demo-five-minute' → …/.failpack/packs/demo-five-minute

==> 2/3  promote → golden
Promoted pack 'demo-five-minute' to golden

==> 3/3  replay — should PASS
RESULT: PASS

Done (~60s). Demo pack left at …/.failpack/packs/demo-five-minute (status=golden).
Clean up with:  failpack rm demo-five-minute --force
Next: failpack demo --claude-hermetic  (prove capture --claude-latest without Claude)  ·  failpack demo --cursor-hermetic  (prove capture --cursor-latest without Cursor)  ·  failpack capture --claude-latest --id my-failure  ·  failpack demo   # full path with break/restore
RESULT: OK
```

Want doctor + intentional FAIL → restore? Run plain `failpack demo` (or
`failpack demo --skip-break` for doctor without the break).

## 3) Readiness score (optional, ~5s)

```bash
$ failpack doctor --score
failpack doctor
  [OK] python: …
  [OK] pyyaml: …
  [OK] claude-projects: not found (…) — optional
         tip: No sessions yet — try: failpack demo --fast  ·  or prove Claude one-shot: failpack demo --claude-hermetic (fake HOME + bundled fixture)  ·  or after a Claude Code run: failpack capture --claude-latest --id my-failure
  [OK] cursor-projects: not found (…) — optional
         tip: No sessions yet — try: failpack demo --fast  ·  or prove Cursor one-shot: failpack demo --cursor-hermetic (fake HOME + bundled fixture)  ·  or after a Cursor agent run: failpack capture --cursor-latest --id cursor-fail
  [OK] layout: .failpack/ + packs/ at …
  [OK] packs: 1 pack(s) (1 golden, 0 captured)

READINESS SCORE: 90/100
checklist:
  [OK] python: …  (+25/25)
  [OK] packs_dir: .failpack/packs/ present  (+25/25)
  [—] claude_projects: not found (optional — fixtures / demo still work)  (+0/5)
  [—] cursor_projects: not found (optional — fixtures / demo still work)  (+0/5)
  [OK] lint: PASS (…)  (+20/20)
  [OK] golden_count: 1 golden pack  (+20/20)
RESULT: OK
```

Score hits **100/100** when both Claude Code (`~/.claude/projects`) and Cursor
(`~/.cursor/projects`) session trees exist **with transcripts**. Either agent
alone adds **+5** with sessions; an **empty** agent projects dir (0 `*.jsonl`)
still adds **+2** half-credit on the score row (soft — not a failure). So a
clean CI-style host may show **90**, and a laptop with an empty
`~/.cursor/projects` may show **92**. Neither agent is required — fixtures and
`failpack demo --fast` are enough. Missing both still yields at least
**90/100** (does not break).

## 4) Forced FAIL → explain → diff

When a fingerprint drifts, strangers should not have to re-read a full replay
dump just to see the text:

```bash
$ echo MUTATED >> .failpack/packs/demo-five-minute/artifacts/error.txt
$ failpack explain demo-five-minute
failpack explain: demo-five-minute
STORY: …
RESULT: FAIL
next: failpack diff demo-five-minute  ·  failpack promote --suggest demo-five-minute  ·  failpack re-promote demo-five-minute

$ failpack diff demo-five-minute
failpack diff: demo-five-minute
  [FAIL] artifacts/error.txt: differ
         diff:
           --- expected/artifacts/error.txt
           +++ artifacts/error.txt
           …
RESULT: FAIL

$ failpack list --json   # or: failpack packs --json
[
  {
    "id": "demo-five-minute",
    "status": "golden",
    …
  }
]
```

## 5) Claude Code one-shot

### 5a) Prove it hermetically (no live Claude Code)

After `pip install failpack` — no clone required. Same discovery as a real
laptop, fake HOME only (bundled fixture ships in the wheel):

```bash
$ failpack demo --claude-hermetic
failpack demo --claude-hermetic  ·  failpack 1.5.11

==> 1/4  seed fake HOME + capture --claude-latest → 'claude-hermetic'
    layout: ~/.claude/projects/<name>/*.jsonl
    fixture → ~/.claude/projects/hermetic-demo/session.jsonl
…
Captured pack 'claude-hermetic' → …/.failpack/packs/claude-hermetic

==> 2/4  promote --suggest --write → golden
…

==> 3/4  lint 'claude-hermetic'
RESULT: PASS

==> 4/4  replay — should PASS
RESULT: PASS

PASS: hermetic Claude one-shot proved (capture --claude-latest without a live Claude install).
Done. Hermetic pack left at …/.failpack/packs/claude-hermetic (status=golden).
Clean up with:  failpack rm claude-hermetic --force
RESULT: OK
```

Checkout alias (thin wrapper): `./examples/claude-latest-hermetic.sh`.

Or the manual fake-HOME dance (also covered in CI). Layout is always
`~/.claude/projects/<name>/*.jsonl` — accept/hermetic demos use
`projects/demo/session.jsonl` or `projects/hermetic-demo/session.jsonl`:

```bash
export HOME=/tmp/failpack-fake-home
mkdir -p "$HOME/.claude/projects/demo"
# from a checkout, or copy from the bundled package data:
cp fixtures/claude-code-failure.jsonl "$HOME/.claude/projects/demo/session.jsonl"
failpack capture --claude-latest --id from-fake-home --force
failpack promote --suggest --write from-fake-home   # applies; no plain promote needed
failpack replay from-fake-home
```

Re-running capture on the same id needs `--force` (or a new `--id`); the
error tip spells both options.

This is **not** a real-user pack — it is the stranger/CI proof that
`--claude-latest` works without inventing fake “user” goldens.

### 5b) Real failure (when you have Claude Code)

After Claude Code fails a task once:

```bash
$ failpack capture --claude-latest --id my-failure
Claude one-shot: newest session under ~/.claude/projects
  using: /home/you/.claude/projects/…/0192ef01-….jsonl
Captured pack 'my-failure' → …/.failpack/packs/my-failure
Next: failpack promote --suggest --write my-failure  (applies; --suggest alone previews)  ·  failpack replay my-failure

$ failpack promote --suggest --write my-failure   # enough — no plain promote needed
$ failpack replay my-failure
```

Doctor tips the same one-shot when sessions are present:

```text
  [OK] claude-projects: found at … (3 sessions)
         tip: One-shot: failpack capture --claude-latest --id my-failure  (newest: 0192ef01-….jsonl)
```

## 6) Cursor one-shot

### 6a) Prove it hermetically (no live Cursor)

After `pip install failpack` — no clone required:

```bash
$ failpack demo --cursor-hermetic
failpack demo --cursor-hermetic  ·  failpack 1.5.11

==> 1/4  seed fake HOME + capture --cursor-latest → 'cursor-hermetic'
    layout: ~/.cursor/projects/<slug>/agent-transcripts/<uuid>/<uuid>.jsonl
    fixture → ~/.cursor/projects/hermetic-demo/agent-transcripts/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl
…
Captured pack 'cursor-hermetic' → …/.failpack/packs/cursor-hermetic

==> 2/4  promote --suggest --write → golden
…

==> 3/4  lint 'cursor-hermetic'
RESULT: PASS

==> 4/4  replay — should PASS
RESULT: PASS

PASS: hermetic Cursor one-shot proved (capture --cursor-latest without a live Cursor install).
Done. Hermetic pack left at …/.failpack/packs/cursor-hermetic (status=golden).
Clean up with:  failpack rm cursor-hermetic --force
RESULT: OK
```

Checkout alias (thin wrapper): `./examples/cursor-latest-hermetic.sh`.

### 6b) Real failure (when you have Cursor)

```bash
$ failpack capture --cursor-latest --id cursor-fail
Captured pack 'cursor-fail' → …/.failpack/packs/cursor-fail
Next: failpack promote --suggest --write cursor-fail  …

$ failpack promote --suggest --write cursor-fail
$ failpack replay cursor-fail
```

## 7) Optional next steps


Use the pack the demo just created (`demo-five-minute`), not repo goldens like
`demo-tool-denied` (those only exist in a FailPack checkout).

```bash
# Preview smarter assertions from the demo pack
failpack promote --suggest demo-five-minute

# Replay every golden pack
failpack replay --all
failpack lint
```

## See also

- [`five-minute-demo.sh`](five-minute-demo.sh) — delegates to `failpack demo`
- [`claude-latest-hermetic.sh`](claude-latest-hermetic.sh) — thin alias for `failpack demo --claude-hermetic`
- [`cursor-latest-hermetic.sh`](cursor-latest-hermetic.sh) — thin alias for `failpack demo --cursor-hermetic`
- [`claude-latest-demo.md`](claude-latest-demo.md) — Claude one-shot detail
- [`cursor-latest-demo.md`](cursor-latest-demo.md)
- [`../docs/SUPPORT.md`](../docs/SUPPORT.md) — GitHub Issues + email
- [`../RELEASE_NOTES_1.5.11.md`](../RELEASE_NOTES_1.5.11.md) — tagged GitHub Release `v1.5.11`
- [`../RELEASE_NOTES_1.5.10.md`](../RELEASE_NOTES_1.5.10.md) — prior Release `v1.5.10`
- [`../RELEASE_NOTES_1.5.9.md`](../RELEASE_NOTES_1.5.9.md) — prior Release `v1.5.9`
- [`../RELEASE_NOTES_1.5.8.md`](../RELEASE_NOTES_1.5.8.md) — prior Release `v1.5.8`
- [`../RELEASE_NOTES_1.5.7.md`](../RELEASE_NOTES_1.5.7.md) — prior Release `v1.5.7`
- [`../RELEASE_NOTES_1.5.6.md`](../RELEASE_NOTES_1.5.6.md) — prior Release `v1.5.6`
- [`../RELEASE_NOTES_1.5.5.md`](../RELEASE_NOTES_1.5.5.md) — prior Release `v1.5.5`
- [`../RELEASE_NOTES_1.5.4.md`](../RELEASE_NOTES_1.5.4.md) — prior Release `v1.5.4`
- [`../RELEASE_NOTES_1.5.3.md`](../RELEASE_NOTES_1.5.3.md) — prior Release `v1.5.3`
- [`../RELEASE_NOTES_1.5.2.md`](../RELEASE_NOTES_1.5.2.md) — prior Release `v1.5.2`
- [`../RELEASE_NOTES_1.5.0.md`](../RELEASE_NOTES_1.5.0.md) — prior Release `v1.5.0`
- [`../RELEASE_NOTES_1.4.0.md`](../RELEASE_NOTES_1.4.0.md) — prior Release `v1.4.0`
- [`../docs/QUALITY_BAR.md`](../docs/QUALITY_BAR.md)
