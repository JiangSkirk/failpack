# Demo: `failpack capture --claude-latest`

Magic path: discover the newest Claude Code session under `~/.claude/projects`
and turn it into a FailPack golden pack — no manual path hunting.

> Tests and CI use a **fake HOME**. This doc shows the real-machine flow.
> FailPack never requires a live agent install in the repo.

## Prerequisites

```bash
pip install -e ".[dev]"
failpack --version    # failpack 0.5.0
failpack doctor
failpack init         # if this repo isn't already initialized
```

Claude Code sessions usually look like:

```text
~/.claude/projects/
  └── <encoded-cwd>/
        ├── 0192abcd-….jsonl      # older
        └── 0192ef01-….jsonl      # newest ← --claude-latest picks this
```

## Screenshots-as-text

### 1) Capture the newest Claude session

```bash
$ failpack capture --claude-latest --id claude-latest-demo --force
Captured pack 'claude-latest-demo' → /…/.failpack/packs/claude-latest-demo
```

Equivalent explicit forms (same newest-jsonl idea):

```bash
failpack capture ~/.claude/projects --id claude-latest-demo --force
failpack capture --from-claude-project ~/.claude/projects --id claude-latest-demo --force
```

### 2) List packs (clean table — no progress noise)

```bash
$ failpack list
ID                     STATUS    EXIT  PROMOTED_AT
---------------------  --------  ----  ----------------------------------------
claude-latest-demo     captured  1     -
demo-missing-import    golden    1     2026-09-14T…
demo-permission-denied golden    13    2026-09-14T…
demo-wrong-test-cmd    golden    4     2026-09-14T…
```

### 3) Promote → replay

```bash
$ failpack promote claude-latest-demo
Promoted pack 'claude-latest-demo' to golden (…/assertions.yaml)

$ failpack replay claude-latest-demo
failpack replay: claude-latest-demo
  [PASS] exit_code: expected 1, got 1
  [PASS] fingerprint:artifacts/error.txt: match
  …
RESULT: PASS
```

### 4) Intentional fix → re-promote

After you fix the underlying bug and accept new golden signals:

```bash
$ failpack replay claude-latest-demo
failpack replay: claude-latest-demo
  [FAIL] fingerprint:artifacts/error.txt: expected abcdef012345… got fedcba987654…
         expected: …
         actual:   …
         hint:     artifact drifted — inspect artifacts/error.txt
RESULT: FAIL

$ failpack re-promote claude-latest-demo
Re-promoted pack 'claude-latest-demo' — refreshed assertions from current artifacts (…/assertions.yaml)

$ failpack replay claude-latest-demo
RESULT: PASS
```

### 5) Replay everything (failure summary)

```bash
$ failpack replay --all
failpack replay --all
  [PASS] demo-missing-import
  [FAIL] claude-latest-demo
    [FAIL] exit_code: expected 1, got 0
           …
SUMMARY: 2 passed, 1 failed (3 golden packs)
  failed packs: claude-latest-demo
  tip: failpack re-promote <id> after intentional fixes
RESULT: FAIL (2/3 golden packs passed)
```

## Cursor paths

Prefer the magic path (best-effort discovery):

```bash
failpack capture --cursor-latest --id cursor-fail
```

See [`cursor-latest-demo.md`](cursor-latest-demo.md) for layout notes and the
fake-HOME testing rule. Manual path still works:

```bash
failpack capture ~/exports/cursor-agent-fail.jsonl --id cursor-fail
failpack capture ~/.cursor/projects --id cursor-fail
```

No Cursor API coupling — same JSONL → pack path as Claude fixtures.

## Fake-HOME tip for contributors

```bash
# never point tests at a real ~/.claude
export HOME=/tmp/failpack-fake-home
mkdir -p "$HOME/.claude/projects/demo"
cp fixtures/claude-code-failure.jsonl "$HOME/.claude/projects/demo/session.jsonl"
failpack capture --claude-latest --id from-fake-home --force
```

See also: [`five-minute-demo.sh`](five-minute-demo.sh), [`CONTRIBUTING.md`](../CONTRIBUTING.md).
