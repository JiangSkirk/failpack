# Stranger walkthrough — FailPack from zero (~60s)

Copy-paste terminal session a new user would see: install from git →
`failpack demo --fast` → optional Claude one-shot. No PyPI token. No Echo /
Orin / titan-agent.

Assumes Python **3.11+** and a clean shell (empty project dir — not the FailPack
repo checkout). Target: **about a minute** to first PASS after install.

## 1) Install from git

```bash
$ pip install "git+https://github.com/JiangSkirk/failpack.git"
Collecting git+https://github.com/JiangSkirk/failpack.git
  …
Successfully installed failpack-1.5.1 …

$ failpack --version
failpack 1.5.1
```

Editable checkout (optional, for contributing):

```bash
$ git clone https://github.com/JiangSkirk/failpack.git
$ cd failpack
$ pip install -e ".[dev]"
$ failpack --version
failpack 1.5.1
```

> Tip: if `failpack: command not found`, add your user scripts dir to `PATH`
> (often `~/.local/bin` after `pip install --user`).

## 2) First wow — `failpack demo --fast` (~60s)

From an **empty** project directory (or any repo without packs yet):

```bash
$ mkdir /tmp/failpack-try && cd /tmp/failpack-try
$ failpack demo --fast
failpack demo --fast  (~60s wow)  ·  failpack 1.5.1

==> 1/3  capture bundled fixture → 'demo-five-minute'
Captured pack 'demo-five-minute' → …/.failpack/packs/demo-five-minute

==> 2/3  promote → golden
Promoted pack 'demo-five-minute' to golden

==> 3/3  replay — should PASS
RESULT: PASS

Done (~60s). Demo pack left at …/.failpack/packs/demo-five-minute (status=golden).
Next: failpack capture --claude-latest --id my-failure  ·  failpack demo   # full path with break/restore
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
         tip: After a Claude Code run: failpack capture --claude-latest --id my-failure  ·  or ~60s wow: failpack demo --fast  ·  or: failpack capture --cursor-latest
  [OK] cursor-projects: not found (…) — optional
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
(`~/.cursor/projects`) session trees exist with transcripts. Either agent alone
adds **+5**; neither is required — fixtures and `failpack demo --fast` are enough.
CI without agent homes stays at **90/100** (does not break).

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

## 5) Claude Code one-shot (when you have a real failure)

After Claude Code fails a task once:

```bash
$ failpack capture --claude-latest --id my-failure
Claude one-shot: newest session under ~/.claude/projects
  using: /home/you/.claude/projects/…/0192ef01-….jsonl
Captured pack 'my-failure' → …/.failpack/packs/my-failure
Next: failpack promote --suggest my-failure  ·  failpack promote --suggest --write my-failure  ·  failpack replay my-failure

$ failpack promote --suggest --write my-failure
$ failpack replay my-failure
```

Doctor tips the same one-shot when sessions are present:

```text
  [OK] claude-projects: found at … (3 sessions)
         tip: One-shot: failpack capture --claude-latest --id my-failure  (newest: 0192ef01-….jsonl)
```

## 6) Optional next steps

Use the pack the demo just created (`demo-five-minute`), not repo goldens like
`demo-tool-denied` (those only exist in a FailPack checkout).

```bash
# Preview smarter assertions from the demo pack
failpack promote --suggest demo-five-minute

# Newest Cursor agent transcript (best-effort; fake HOME in tests)
failpack capture --cursor-latest --id cursor-fail

# Replay every golden pack
failpack replay --all
failpack lint
```

## See also

- [`five-minute-demo.sh`](five-minute-demo.sh) — delegates to `failpack demo`
- [`claude-latest-demo.md`](claude-latest-demo.md) — Claude one-shot detail
- [`cursor-latest-demo.md`](cursor-latest-demo.md)
- [`../RELEASE_NOTES_1.5.0.md`](../RELEASE_NOTES_1.5.0.md) — tagged GitHub Release `v1.5.0`
- [`../docs/QUALITY_BAR.md`](../docs/QUALITY_BAR.md) — honest sell-ready gaps
- [`../CHANGELOG.md`](../CHANGELOG.md)
