# Contributing to FailPack

Thanks for helping keep agent failure memory honest.

## Principles

- **Narrow job:** capture a real failure session → promote golden assertions → replay in CI.
- **Fixtures only:** zero coupling to Echo, Orin, titan-agent, or any live agent install.
- **No monetization in-tree product surface** for this line of work — keep the open CLI useful.
- **Tests never require a real `~/.claude`.** Use a fake `HOME` (or pass `home=` to discovery helpers).

## Setup

Requires Python **3.11+**.

```bash
pip install -e ".[dev]"
failpack --version   # → failpack 0.5.0
failpack doctor
pytest -q
```

## Workflow

1. Branch from `main`.
2. Make a focused change (one wow gap or bugfix).
3. Add / update tests under `tests/`.
4. Run `pytest -q` and `failpack replay --all`.
5. If you touch capture discovery, cover it with a **fake HOME** fixture.
6. Update `CHANGELOG.md` under the next version section.
7. Open a PR with a short “why” and how you verified.

## Layout

| Path | Role |
|---|---|
| `src/failpack/` | CLI + library |
| `tests/` | pytest suite |
| `fixtures/` | Claude-Code-like JSONL fixtures |
| `.failpack/packs/` | Shipped golden demo packs |
| `examples/` | Smoke demos and CI snippets |

## Magic capture (`--claude-latest`)

Claude Code sessions typically live at:

```text
~/.claude/projects/<encoded-cwd>/*.jsonl
```

`failpack capture --claude-latest` picks the newest `*.jsonl` under that tree.
In tests, build a temporary home:

```python
home = tmp_path / "fake-home"
(home / ".claude" / "projects" / "proj").mkdir(parents=True)
# write *.jsonl under proj, then:
cmd_capture(claude_latest=True, home=home, ...)
```

### Cursor-ish paths (optional, safe docs only)

FailPack does **not** auto-scan Cursor installs. If you export or copy a Cursor
agent transcript as JSONL, capture it like any other file:

```bash
failpack capture /path/to/exported-session.jsonl --id cursor-fail
```

Some Cursor / agent setups keep project-local logs under paths resembling
`~/.cursor/projects/` or workspace `.cursor/` folders — treat those as **manual**
inputs (pass the file or directory explicitly). Do not add live Cursor API coupling.

## Re-promote after intentional drift

```bash
failpack replay my-failure          # FAIL after you fixed the bug intentionally
# update artifacts if needed, then:
failpack re-promote my-failure      # refresh assertions.yaml + expected/
failpack replay my-failure          # PASS
```

## Style

- Prefer small, readable modules (`commands_*.py`).
- Plain `argparse` (no Click/Typer unless the project switches).
- Respect `NO_COLOR` / `FORCE_COLOR` for ANSI.
- Keep CLI output progress-free for `list` (aligned table only).

## License

MIT — by contributing, you agree your changes are MIT-licensed.
