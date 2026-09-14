# Demo: `failpack capture --claude-latest` (Claude Code one-shot)

Magic path: discover the newest Claude Code session under `~/.claude/projects`
and turn it into a FailPack golden pack — no manual path hunting.

## Prove it without a live Claude install (first-class)

Strangers and CI should **not** invent fake “user” packs. After
`pip install failpack`, prove `capture --claude-latest` with a **fake HOME**
plus the **bundled** fixture — no clone required:

```bash
pip install failpack
failpack demo --claude-hermetic
# optional: failpack demo --claude-hermetic --fast
```

Checkout alias (thin wrapper):

```bash
./examples/claude-latest-hermetic.sh
```

That path seeds `~/.claude/projects/<name>/*.jsonl` (here
`projects/hermetic-demo/session.jsonl`) from the shipped fixture, then runs
**capture --claude-latest → promote --suggest --write → lint → replay**. Or do
it by hand (layout is always `~/.claude/projects/<name>/*.jsonl` — accept used
`projects/demo/session.jsonl`):

```bash
export HOME=/tmp/failpack-fake-home
mkdir -p "$HOME/.claude/projects/demo"
cp fixtures/claude-code-failure.jsonl "$HOME/.claude/projects/demo/session.jsonl"
failpack capture --claude-latest --id from-fake-home --force
failpack promote --suggest --write from-fake-home   # applies; plain promote not needed
failpack replay from-fake-home
```

Re-capture the same id? Pass `--force` or pick a new `--id` — the error tip says both.

Doctor tips the same path when no sessions exist (`demo --fast` /
`demo --claude-hermetic` first). FailPack never requires a live agent install
in the repo.

## Real-machine one-shot (~a minute after a real failure)

```bash
failpack capture --claude-latest --id my-failure
failpack promote --suggest --write my-failure   # applies (enough — no plain promote needed)
failpack replay my-failure
```

On capture success you should see:

```text
Claude one-shot: newest session under ~/.claude/projects
  using: /home/you/.claude/projects/…/0192ef01-….jsonl
Captured pack 'my-failure' → …/.failpack/packs/my-failure
Next: failpack promote --suggest --write my-failure  (applies; --suggest alone previews)  ·  failpack replay my-failure
```

No Claude sessions yet? Doctor and the error message both tip:

```bash
failpack demo --fast                    # ~60s wow without an agent
failpack demo --claude-hermetic         # prove --claude-latest hermetically
# or finish a Claude Code run, then retry --claude-latest
```

## Prerequisites

```bash
pip install failpack   # or: pip install -e ".[dev]"
failpack --version    # failpack 1.5.9+
failpack doctor       # tips hermetic path when no sessions; --claude-latest when sessions exist
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
Claude one-shot: newest session under ~/.claude/projects
  using: /…/.claude/projects/…/0192ef01-….jsonl
Captured pack 'claude-latest-demo' → /…/.failpack/packs/claude-latest-demo
Next: failpack promote --suggest claude-latest-demo  ·  …
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
$ failpack promote --suggest --write claude-latest-demo
Promoted pack 'claude-latest-demo' to golden (…/assertions.yaml)
# --suggest --write is enough; plain `promote` after that is redundant (idempotent)

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
next: failpack explain claude-latest-demo  ·  failpack promote --suggest claude-latest-demo  ·  failpack re-promote claude-latest-demo

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
  tip: failpack explain <id>  ·  failpack promote --suggest <id>  ·  failpack re-promote <id>
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

## See also

- [`claude-latest-hermetic.sh`](claude-latest-hermetic.sh) — thin alias for `failpack demo --claude-hermetic`
- [`STRANGER_WALKTHROUGH.md`](STRANGER_WALKTHROUGH.md)
- [`five-minute-demo.sh`](five-minute-demo.sh)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
