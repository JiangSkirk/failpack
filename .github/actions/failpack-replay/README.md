# FailPack replay (composite action)

Install FailPack and replay every golden pack under `.failpack/packs/`
(`failpack replay --all`). Use this from **any** repo that vendors FailPack packs.

## Usage

### This FailPack repo (editable install)

```yaml
- uses: ./.github/actions/failpack-replay
  with:
    install-from: "."
    run-doctor: "true"
```

### Other repos (install from GitHub)

**Prefer a release tag** (stable CLI once `v1.1.0` exists):

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.1.0
  with:
    # default install-from is git+https://github.com/JiangSkirk/failpack.git
    run-doctor: "true"
```

`@main` remains a valid alternative when you want the tip of the default branch
(may move):

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@main
```

Older tag still available: `@v1.0.0`.

### Machine-readable replay

```yaml
- uses: JiangSkirk/failpack/.github/actions/failpack-replay@v1.1.0
  with:
    json: "true"
```

Full workflow example: [`examples/other-repo-ci.yml`](../../../examples/other-repo-ci.yml).

## Inputs

| Input | Default | Description |
|---|---|---|
| `root` | `"."` | Project root containing `.failpack/` |
| `python-version` | `"3.12"` | Python version for `actions/setup-python` |
| `install-from` | `git+https://github.com/JiangSkirk/failpack.git` | `"."` for editable local install, or a pip URL |
| `extra-pip-args` | `""` | Extra args passed to `pip install` |
| `run-doctor` | `"true"` | Run `failpack doctor --score` before replay (advisory; exits 0) |
| `run-lint` | `"true"` | Run `failpack lint` before replay (layout + assertion schema; no replay) |
| `json` | `"false"` | Emit `failpack replay --all --json` |
| `step-summary` | `"true"` | Write `failpack report --github` to `$GITHUB_STEP_SUMMARY` |

### Step summary shape

With `step-summary: "true"` (default), the Actions **job summary** gets markdown like:

```markdown
# FailPack replay

| Pack | Result | Checks |
| --- | --- | --- |
| `demo-missing-import` | **PASS** | 5/5 |

## Failures
### `some-pack`
> STORY: Pack 'some-pack' failed …
- **FAIL** `fingerprint:artifacts/error.txt`: …
```

## Outputs

This composite action does **not** set `outputs:` — the CI signal is the step
exit code:

| Result | Meaning |
|---|---|
| exit `0` | All golden packs passed (or none found) |
| non-zero | At least one golden pack failed replay (or lint errored) |

Inspect the job log for `failpack list` + per-pack PASS/FAIL lines (or JSON when
`json: "true"`). The Actions **job summary** gets a markdown table from
`failpack report` when `step-summary` is enabled. Use `failpack explain <id>`
locally for the short FAIL story.

## What it runs

1. `actions/setup-python` at `python-version`
2. `pip install` FailPack from `install-from`
3. Optional `failpack doctor --score` (advisory readiness checklist)
4. Optional `failpack lint` (`run-lint`, default on)
5. `failpack list` + `failpack replay --all` (or `--json`)
6. Optional `failpack report --github` (`step-summary`, default on; always runs after replay)

## Related

- Repo workflow dogfood: [`.github/workflows/failpack-replay.yml`](../../workflows/failpack-replay.yml)
- CLI: `failpack show <id>`, `failpack replay --all`, `failpack explain`, `failpack report`, `failpack lint`, `failpack demo`
- Pack index: [`docs/PACKS.md`](../../../docs/PACKS.md)
