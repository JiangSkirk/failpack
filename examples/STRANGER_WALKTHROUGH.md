# Stranger walkthrough — FailPack from zero

Copy-paste terminal session a new user would see: install from git → demo →
`doctor --score`. No PyPI token. No Echo / Orin / titan-agent.

Assumes Python **3.11+** and a clean shell (empty project dir — not the FailPack
repo checkout).

## 1) Install from git

```bash
$ pip install "git+https://github.com/JiangSkirk/failpack.git"
Collecting git+https://github.com/JiangSkirk/failpack.git
  …
Successfully installed failpack-1.2.0 …

$ failpack --version
failpack 1.2.0
```

Editable checkout (optional, for contributing):

```bash
$ git clone https://github.com/JiangSkirk/failpack.git
$ cd failpack
$ pip install -e ".[dev]"
$ failpack --version
failpack 1.2.0
```

> Tip: if `failpack: command not found`, add your user scripts dir to `PATH`
> (often `~/.local/bin` after `pip install --user`).

## 2) First wow — `failpack demo`

From an **empty** project directory (or any repo without packs yet):

```bash
$ mkdir /tmp/failpack-try && cd /tmp/failpack-try
$ failpack demo --skip-break
==> 1/8  failpack --version (expect 1.2.0)
failpack 1.2.0

==> 2/8  doctor — env + .failpack/ layout
failpack doctor
  [OK] python: 3.12.3 (>= 3.11 required)
  [OK] pyyaml: importable (version 6.0.1)
  [OK] claude-projects: not found (/home/you/.claude/projects) — optional
         tip: Install/use Claude Code, or capture a fixture / exported JSONL. Try: failpack demo · or: failpack capture --cursor-latest
  [OK] cursor-projects: not found (/home/you/.cursor/projects) — optional
         tip: Use Cursor agent transcripts, or capture a fixture / exported JSONL. Try: failpack demo · or: failpack capture --claude-latest
  [OK] layout: .failpack/ + packs/ at …/.failpack
  [OK] packs: 0 packs — capture a transcript to get started
         tip: failpack demo   # or: failpack capture --claude-latest / --cursor-latest --id my-failure
RESULT: OK

==> 3/8  capture bundled fixture → pack 'demo-five-minute'
Captured pack 'demo-five-minute' → …/.failpack/packs/demo-five-minute

==> 4/8  promote → golden assertions.yaml
failpack status: demo-five-minute
  status:       golden
  …
  assertions:
    - exit_code == 1
    - min_events >= 11
    - 7 fingerprint(s)
    - …

==> 5/8  replay — should PASS
failpack replay: demo-five-minute
  [PASS] exit_code: expected 1, got 1
  …
RESULT: PASS

==> 6–7/8  skipped intentional break (--skip-break)

==> 8/8  migrate (should no-op — already current)
failpack migrate (schema v1)
  already at schema version 1 (…) — nothing to do

Done. Demo pack left at …/.failpack/packs/demo-five-minute (status=golden).
RESULT: OK
```

Omit `--skip-break` to see the intentional FAIL → restore PASS loop. On FAIL,
replay prints a one-line `next:` tip:

```text
RESULT: FAIL
next: failpack explain demo-five-minute  ·  failpack promote --suggest demo-five-minute  ·  failpack re-promote demo-five-minute
```

## 3) Readiness score

```bash
$ failpack doctor --score
failpack doctor
  [OK] python: …
  [OK] pyyaml: …
  [OK] claude-projects: not found (…) — optional
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
adds **+5**; neither is required — fixtures and `failpack demo` are enough.
CI without agent homes stays at **90/100** (does not break).

## 4) Optional next steps

Use the pack the demo just created (`demo-five-minute`), not repo goldens like
`demo-tool-denied` (those only exist in a FailPack checkout).

```bash
# Preview smarter assertions from the demo pack
failpack promote --suggest demo-five-minute

# Apply suggestions
failpack promote --suggest --write demo-five-minute

# Newest Claude Code session
failpack capture --claude-latest --id my-failure

# Newest Cursor agent transcript (best-effort; fake HOME in tests)
failpack capture --cursor-latest --id cursor-fail

# Replay every golden pack
failpack replay --all
failpack lint
```

## See also

- [`five-minute-demo.sh`](five-minute-demo.sh)
- [`claude-latest-demo.md`](claude-latest-demo.md)
- [`cursor-latest-demo.md`](cursor-latest-demo.md)
- [`../RELEASE_NOTES_1.1.0.md`](../RELEASE_NOTES_1.1.0.md) — tagged GitHub Release `v1.1.0`
- [`../CHANGELOG.md`](../CHANGELOG.md)
