# Stranger walkthrough — FailPack from zero

Copy-paste terminal session a new user would see: install from git → demo →
`doctor --score`. No PyPI token. No Echo / Orin / titan-agent.

Assumes Python **3.11+** and a clean shell.

## 1) Install from git

```bash
$ pip install "git+https://github.com/JiangSkirk/failpack.git"
Collecting git+https://github.com/JiangSkirk/failpack.git
  …
Successfully installed failpack-1.1.0 …

$ failpack --version
failpack 1.1.0
```

Editable checkout (optional, for contributing):

```bash
$ git clone https://github.com/JiangSkirk/failpack.git
$ cd failpack
$ pip install -e ".[dev]"
$ failpack --version
failpack 1.1.0
```

## 2) First wow — `failpack demo`

```bash
$ failpack demo --skip-break
==> 1/8  failpack --version (expect 1.1.0)
failpack 1.1.0

==> 2/8  doctor — env + .failpack/ layout
failpack doctor
  [OK] python: 3.12.3 (>= 3.11 required)
  [OK] pyyaml: importable (version 6.0.1)
  [OK] claude-projects: not found (/home/you/.claude/projects) — optional
         tip: Install/use Claude Code, or capture a fixture / exported JSONL. Try: failpack demo
  [OK] layout: .failpack/ + packs/ at …/.failpack
  [OK] packs: 4 pack(s) (4 golden, 0 captured)
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

Omit `--skip-break` to see the intentional FAIL → restore PASS loop.

## 3) Readiness score

```bash
$ failpack doctor --score
failpack doctor
  [OK] python: 3.12.3 (>= 3.11 required)
  [OK] pyyaml: importable (version 6.0.1)
  [OK] claude-projects: not found (…) — optional
  [OK] layout: .failpack/ + packs/ at …
  [OK] packs: … pack(s) (… golden, … captured)

READINESS SCORE: 90/100
checklist:
  [OK] python: …  (+25/25)
  [OK] packs_dir: .failpack/packs/ present  (+25/25)
  [—] claude_projects: not found (optional — fixtures / demo still work)  (+0/10)
  [OK] lint: PASS (…)  (+20/20)
  [OK] golden_count: … golden packs  (+20/20)
RESULT: OK
```

Score hits **100/100** when Claude Code sessions exist under `~/.claude/projects`
(optional — fixtures and `failpack demo` are enough to get value).

## 4) Optional next steps

```bash
# Preview smarter assertions from a captured pack
failpack promote --suggest demo-tool-denied

# Apply suggestions
failpack promote --suggest --write my-failure

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
- [`../RELEASE_NOTES_1.0.0.md`](../RELEASE_NOTES_1.0.0.md) — tagged GitHub Release `v1.0.0`
- [`../CHANGELOG.md`](../CHANGELOG.md)
