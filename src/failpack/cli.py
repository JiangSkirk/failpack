"""FailPack CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from failpack import __version__
from failpack.commands_capture import cmd_capture
from failpack.commands_completion import cmd_completion
from failpack.commands_demo import cmd_demo
from failpack.commands_doctor import cmd_doctor
from failpack.commands_explain import cmd_explain
from failpack.commands_export import cmd_export
from failpack.commands_import import cmd_import
from failpack.commands_init import cmd_init
from failpack.commands_lint import cmd_lint
from failpack.commands_list import cmd_list, format_table
from failpack.commands_migrate import cmd_migrate
from failpack.commands_promote import (
    cmd_promote,
    cmd_re_promote,
    format_assertions_preview,
    format_suggest_preview,
)
from failpack.commands_rename import cmd_rename
from failpack.commands_replay import cmd_replay, cmd_replay_all
from failpack.commands_report import cmd_report
from failpack.commands_rm import cmd_rm
from failpack.commands_show import cmd_show
from failpack.commands_status import cmd_status
from failpack.commands_watch import cmd_watch
from failpack.license import cmd_license_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="failpack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "FailPack: turn coding-agent failure sessions "
            "into golden CI regression packs."
        ),
        epilog=(
            "examples:\n"
            "  failpack demo\n"
            "  failpack doctor --score\n"
            "  failpack capture --claude-latest --id my-failure\n"
            "  failpack capture --cursor-latest --id my-failure\n"
            "  failpack promote my-failure && failpack replay my-failure\n"
            "  failpack export my-failure -o my-failure.tgz\n"
            "  failpack import my-failure.tgz\n"
            "  failpack replay --all\n"
            "  failpack list\n"
            "  failpack show demo-missing-import\n"
            "  failpack report --github\n"
            "  failpack explain my-failure\n"
            "  failpack lint\n"
            "  failpack promote --dry-run my-failure\n"
            "  failpack promote --suggest my-failure\n"
            "  failpack rename old-id new-id\n"
            "  failpack rm my-failure --force\n"
            "  failpack completion bash\n"
            "  failpack migrate\n"
            "  failpack init --ci\n"
            "\n"
            "install (no PyPI required):\n"
            '  pip install "git+https://github.com/JiangSkirk/failpack.git"\n'
            "  failpack demo\n"
            "\n"
            "environment:\n"
            "  NO_COLOR      disable ANSI colors\n"
            "  FORCE_COLOR   force ANSI colors even when not a TTY\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"failpack {__version__}")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root containing .failpack/ (default: walk from cwd)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create .failpack/ workspace layout",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack init\n"
            "  failpack init --ci\n"
            "  failpack --root /path/to/project init --ci\n"
        ),
    )
    p_init.add_argument(
        "--ci",
        action="store_true",
        help="Also write a starter .github/workflows/failpack.yml using the composite action",
    )
    p_init.set_defaults(func=_handle_init)

    p_doctor = sub.add_parser(
        "doctor",
        help="Check env + workspace; optional --score readiness (0–100)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack doctor\n"
            "  failpack doctor --score\n"
            "  failpack doctor --score --strict\n"
            "\n"
            "Checks Python, PyYAML, ~/.claude/projects, .failpack/ layout, packs.\n"
            "--score adds a 0–100 readiness score + checklist (python, packs_dir,\n"
            "claude_projects, cursor_projects, lint, golden_count).\n"
            "Agent paths are soft (missing Claude/Cursor does not break CI).\n"
            "Exit 0 always unless --strict (then non-zero when RESULT: FAIL).\n"
        ),
    )
    p_doctor.add_argument(
        "--score",
        action="store_true",
        help="Print a 0–100 readiness score and checklist",
    )
    p_doctor.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any doctor check FAILs (default: always exit 0)",
    )
    p_doctor.set_defaults(func=_handle_doctor)

    p_demo = sub.add_parser(
        "demo",
        help="One-command five-minute wow path (capture → promote → replay)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack demo\n"
            "  failpack demo --no-keep\n"
            "  failpack demo --skip-break\n"
            "\n"
            'Zero-setup: pip install "git+https://github.com/JiangSkirk/failpack.git"\n'
            "             && failpack demo\n"
            "Uses a bundled fixture (same path as examples/five-minute-demo.sh).\n"
        ),
    )
    p_demo.add_argument(
        "--id",
        dest="pack_id",
        default=None,
        help="Demo pack id (default: demo-five-minute)",
    )
    p_demo.add_argument(
        "--no-keep",
        action="store_true",
        help="Remove the demo pack when finished",
    )
    p_demo.add_argument(
        "--skip-break",
        action="store_true",
        help="Skip the intentional artifact break / restore steps",
    )
    p_demo.set_defaults(func=_handle_demo)

    p_export = sub.add_parser(
        "export",
        help="Tar/zip a golden pack for sharing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack export demo-missing-import\n"
            "  failpack export demo-missing-import -o pack.tgz\n"
            "  failpack export demo-missing-import -o pack.zip\n"
            "\n"
            "Archive includes assertions + expected + meta + artifacts + transcript.\n"
        ),
    )
    p_export.add_argument("pack_id", help="Golden pack id under .failpack/packs/")
    p_export.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        metavar="PATH",
        help="Output archive path (default: <id>.tgz); .zip / .tgz / .tar.gz",
    )
    p_export.set_defaults(func=_handle_export)

    p_import = sub.add_parser(
        "import",
        help="Restore a shared pack archive into .failpack/packs/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack import pack.tgz\n"
            "  failpack import pack.tgz --force\n"
            "  failpack import pack.tgz --rename my-copy\n"
            "\n"
            "On id collision: --force overwrites, or --rename <id> imports under a new id.\n"
        ),
    )
    p_import.add_argument("archive", type=Path, help="Path to pack.tgz / .tar.gz / .zip")
    p_import.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing pack with the same id",
    )
    p_import.add_argument(
        "--rename",
        dest="rename",
        default=None,
        metavar="ID",
        help="Import under a different pack id",
    )
    p_import.set_defaults(func=_handle_import)

    p_list = sub.add_parser(
        "list",
        help="List packs under .failpack/packs/ (clean table)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  failpack list\n",
    )
    p_list.set_defaults(func=_handle_list)

    p_status = sub.add_parser(
        "status",
        help="Show meta + assertion summary for one pack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  failpack status demo-missing-import\n",
    )
    p_status.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_status.set_defaults(func=_handle_status)

    p_show = sub.add_parser(
        "show",
        help="Pretty inspect one pack (status, asserts, artifacts)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack show demo-missing-import\n"
            "  failpack show demo-tool-denied --json\n"
            "\n"
            "Prints status, exit, promoted_at, assertion summary, and artifact list.\n"
        ),
    )
    p_show.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_show.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human summary lines",
    )
    p_show.set_defaults(func=_handle_show)

    p_cap = sub.add_parser(
        "capture",
        help="Ingest a Claude-Code-like JSONL transcript",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack capture --claude-latest --id my-failure\n"
            "  failpack capture --cursor-latest --id my-failure\n"
            "  failpack capture fixtures/claude-code-failure.jsonl --id my-failure\n"
            "  failpack capture ~/.claude/projects --id my-failure\n"
            "  failpack capture --from-claude-project ~/.claude/projects\n"
            "  failpack capture --stdin < session.jsonl\n"
            "  failpack capture 'fixtures/*.jsonl' --id from-glob\n"
            "\n"
            "magic: --claude-latest finds the newest *.jsonl under\n"
            "~/.claude/projects (Claude Code). --cursor-latest finds the newest\n"
            "agent transcript under ~/.cursor/projects/*/agent-transcripts\n"
            "(best-effort). A bare directory argument also picks the newest\n"
            "*.jsonl underneath.\n"
        ),
    )
    p_cap.add_argument(
        "transcript",
        type=Path,
        nargs="?",
        default=None,
        help=(
            "Path to transcript.jsonl, or a directory (newest *.jsonl inside); "
            "supports shell globs; use - for stdin"
        ),
    )
    p_cap.add_argument("--id", dest="pack_id", default=None, help="Pack id (default: from transcript)")
    p_cap.add_argument("--force", action="store_true", help="Overwrite existing pack")
    p_cap.add_argument(
        "--claude-latest",
        action="store_true",
        help="Discover newest Claude Code session under ~/.claude/projects",
    )
    p_cap.add_argument(
        "--cursor-latest",
        action="store_true",
        help=(
            "Discover newest Cursor agent transcript under "
            "~/.cursor/projects/*/agent-transcripts (best-effort)"
        ),
    )
    p_cap.add_argument(
        "--from-claude-project",
        type=Path,
        default=None,
        metavar="PATH",
        help="Find newest *.jsonl under a Claude Code projects directory",
    )
    p_cap.add_argument(
        "--stdin",
        action="store_true",
        help="Read transcript JSONL from stdin",
    )
    p_cap.add_argument(
        "--glob",
        dest="pattern",
        default=None,
        metavar="PATTERN",
        help="Glob for transcript files (picks newest if multiple match)",
    )
    p_cap.set_defaults(func=_handle_capture)

    p_prom = sub.add_parser(
        "promote",
        help="Mark pack golden and write assertions.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack promote my-failure\n"
            "  failpack promote --suggest my-failure\n"
            "  failpack promote --suggest --write my-failure\n"
            "  failpack promote --dry-run my-failure\n"
            "  failpack promote my-failure --dry-run\n"
            "  failpack re-promote my-failure   # refresh after intentional fix\n"
            "\n"
            "--suggest analyzes artifacts + transcript ticks and prints\n"
            "recommended assertions (exit_code, fingerprint paths,\n"
            "tool_denied_contains, bash_output_contains). Add --write to apply.\n"
            "Plain promote writes the same smarter suggestions.\n"
        ),
    )
    p_prom.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_prom.add_argument(
        "--dry-run",
        action="store_true",
        help="Print assertions that would be written without writing",
    )
    p_prom.add_argument(
        "--suggest",
        action="store_true",
        help=(
            "Analyze transcript/artifacts and print recommended assertions "
            "(preview; add --write to apply)"
        ),
    )
    p_prom.add_argument(
        "--write",
        action="store_true",
        help="With --suggest: write the recommended assertions.yaml",
    )
    p_prom.set_defaults(func=_handle_promote)

    p_reprom = sub.add_parser(
        "re-promote",
        help="Refresh golden assertions from current artifacts (after intentional fix)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack re-promote my-failure\n"
            "  failpack re-promote --suggest my-failure\n"
            "  failpack re-promote --suggest --write my-failure\n"
            "  failpack re-promote --dry-run my-failure\n"
            "\n"
            "Use after replay FAIL when the new artifact signals are intentional:\n"
            "rewrites assertions.yaml + expected/ snapshots from current artifacts.\n"
        ),
    )
    p_reprom.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_reprom.add_argument(
        "--dry-run",
        action="store_true",
        help="Print assertions that would be written without writing",
    )
    p_reprom.add_argument(
        "--suggest",
        action="store_true",
        help="Preview smarter assertion suggestions without writing",
    )
    p_reprom.add_argument(
        "--write",
        action="store_true",
        help="With --suggest: write the recommended assertions.yaml",
    )
    p_reprom.set_defaults(func=_handle_re_promote)

    p_watch = sub.add_parser(
        "watch",
        help="Capture → promote → replay (local pre-commit / docs helper)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack watch fixtures/claude-code-failure.jsonl --id my-failure\n"
            "  failpack watch --claude-latest --id latest --force\n"
            "  failpack watch --cursor-latest --id latest --force\n"
            "  failpack watch ~/.claude/projects --id latest --force\n"
            "\n"
            "On replay FAIL, prints explain (expected/actual/hint + optional diff) and exits 1.\n"
        ),
    )
    p_watch.add_argument(
        "transcript",
        type=Path,
        nargs="?",
        default=None,
        help="Transcript path, directory, or - for stdin (same as capture)",
    )
    p_watch.add_argument("--id", dest="pack_id", default=None, help="Pack id (default: from transcript)")
    p_watch.add_argument("--force", action="store_true", help="Overwrite existing pack")
    p_watch.add_argument(
        "--claude-latest",
        action="store_true",
        help="Discover newest Claude Code session under ~/.claude/projects",
    )
    p_watch.add_argument(
        "--cursor-latest",
        action="store_true",
        help=(
            "Discover newest Cursor agent transcript under "
            "~/.cursor/projects/*/agent-transcripts (best-effort)"
        ),
    )
    p_watch.add_argument(
        "--from-claude-project",
        type=Path,
        default=None,
        metavar="PATH",
        help="Find newest *.jsonl under a Claude Code projects directory",
    )
    p_watch.add_argument("--stdin", action="store_true", help="Read transcript JSONL from stdin")
    p_watch.add_argument(
        "--glob",
        dest="pattern",
        default=None,
        metavar="PATTERN",
        help="Glob for transcript files (picks newest if multiple match)",
    )
    p_watch.add_argument(
        "--no-diff",
        action="store_true",
        help="Disable unified diffs under fingerprint FAIL blocks",
    )
    p_watch.set_defaults(func=_handle_watch)

    p_rep = sub.add_parser(
        "replay",
        help="Verify golden assertions (exit 0 pass / non-zero fail)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack replay demo-missing-import\n"
            "  failpack replay --all\n"
            "  failpack replay --all --json\n"
            "  failpack replay demo-missing-import --json\n"
            "  failpack replay demo-missing-import --no-diff\n"
            "\n"
            "On failure, human output prints expected vs actual plus a one-line hint\n"
            "(e.g. re-promote after intentional change / artifact drifted — inspect path),\n"
            "then a short STORY block (what broke / which assertion / what to do next).\n"
            "Fingerprint failures also show a short unified diff of expected vs actual\n"
            "artifact text when a promote-time snapshot exists (disable with --no-diff).\n"
            "replay --all ends with SUMMARY (passed/failed counts) and failed pack ids.\n"
            "Prefer `failpack explain <id>` when you only want the story.\n"
            "Colors are on for TTYs; set NO_COLOR=1 to disable.\n"
        ),
    )
    p_rep.add_argument(
        "pack_id",
        nargs="?",
        default=None,
        help="Pack id under .failpack/packs/ (omit when using --all)",
    )
    p_rep.add_argument(
        "--all",
        action="store_true",
        help="Replay every golden pack; exit non-zero if any fail",
    )
    p_rep.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human summary lines",
    )
    p_rep.add_argument(
        "--no-diff",
        action="store_true",
        help="Disable unified diffs under fingerprint FAIL blocks",
    )
    p_rep.set_defaults(func=_handle_replay)

    p_explain = sub.add_parser(
        "explain",
        help="Short narrative for a replay FAIL (what / assert / next)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack explain demo-missing-import\n"
            "  failpack explain                 # every currently failing golden\n"
            "\n"
            "Replays assertions (no verbose check dump) and prints one STORY:\n"
            "what broke, which assertion, what to do next.\n"
            "Exit 0 on PASS, non-zero on FAIL (same signal as replay).\n"
        ),
    )
    p_explain.add_argument(
        "pack_id",
        nargs="?",
        default=None,
        help="Pack id (default: explain every failing golden pack)",
    )
    p_explain.set_defaults(func=_handle_explain)

    p_report = sub.add_parser(
        "report",
        help="Markdown replay summary (GitHub Actions step summary)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack report                 # all golden packs → markdown on stdout\n"
            "  failpack report demo-missing-import\n"
            "  failpack report --github        # append to $GITHUB_STEP_SUMMARY\n"
            "  failpack report -o report.md\n"
            "\n"
            "Exit 0 on PASS, non-zero on FAIL (same signal as replay).\n"
        ),
    )
    p_report.add_argument(
        "pack_id",
        nargs="?",
        default=None,
        help="Pack id (default: all golden packs)",
    )
    p_report.add_argument(
        "--github",
        action="store_true",
        help="Append markdown to $GITHUB_STEP_SUMMARY (GitHub Actions)",
    )
    p_report.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write markdown to a file instead of stdout",
    )
    p_report.add_argument(
        "--no-diff",
        action="store_true",
        help="Omit fingerprint diffs in the markdown report",
    )
    p_report.set_defaults(func=_handle_report)

    p_lint = sub.add_parser(
        "lint",
        help="Validate pack layout + assertion schema (no replay)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack lint\n"
            "  failpack lint demo-missing-import\n"
            "\n"
            "Checks meta/assertions schema, id consistency, and golden layout.\n"
            "Exit 0 when no errors (warnings allowed).\n"
        ),
    )
    p_lint.add_argument(
        "pack_id",
        nargs="?",
        default=None,
        help="Pack id (default: every pack under .failpack/packs/)",
    )
    p_lint.set_defaults(func=_handle_lint)

    p_mig = sub.add_parser(
        "migrate",
        help="Stamp pack schema_version (no-op if already current)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  failpack migrate\n",
    )
    p_mig.set_defaults(func=_handle_migrate)

    p_rm = sub.add_parser(
        "rm",
        help="Delete a pack directory (refuses golden without --force)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack rm my-failure\n"
            "  failpack rm my-failure --force   # required when status is golden\n"
        ),
    )
    p_rm.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_rm.add_argument(
        "--force",
        action="store_true",
        help="Allow deleting a golden pack",
    )
    p_rm.set_defaults(func=_handle_rm)

    p_rename = sub.add_parser(
        "rename",
        help="Rename a pack id and update meta (+ assertions pack_id)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack rename old-id new-id\n"
        ),
    )
    p_rename.add_argument("old_id", help="Current pack id")
    p_rename.add_argument("new_id", help="New pack id")
    p_rename.set_defaults(func=_handle_rename)

    p_comp = sub.add_parser(
        "completion",
        help="Print shell completion script (bash|zsh)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  eval \"$(failpack completion bash)\"\n"
            "  failpack completion zsh > \"${fpath[1]}/_failpack\"\n"
        ),
    )
    p_comp.add_argument(
        "shell",
        choices=("bash", "zsh"),
        help="Shell to generate completion for",
    )
    p_comp.set_defaults(func=_handle_completion)

    p_lic = sub.add_parser("license", help="License helpers for future Pro gating")
    lic_sub = p_lic.add_subparsers(dest="license_cmd", required=True)
    p_lic_check = lic_sub.add_parser("check", help="Validate FAILPACK_LICENSE (HMAC stub)")
    p_lic_check.set_defaults(func=_handle_license_check)

    return parser


def _handle_init(args: argparse.Namespace) -> int:
    path, workflow = cmd_init(args.root, ci=args.ci)
    print(f"Initialized FailPack workspace at {path}")
    if args.ci:
        if workflow and workflow.exists():
            print(f"CI workflow: {workflow}")
        else:
            print("CI workflow: (unchanged)")
    return 0


def _handle_doctor(args: argparse.Namespace) -> int:
    report = cmd_doctor(args.root, score=args.score)
    print("\n".join(report.summary_lines(with_score=args.score)))
    # Stranger-friendly: doctor is advisory by default (exit 0).
    if args.strict and not report.ok:
        return 1
    return 0


def _handle_demo(args: argparse.Namespace) -> int:
    from failpack.commands_demo import DEMO_PACK_ID

    report = cmd_demo(
        root=args.root,
        pack_id=args.pack_id or DEMO_PACK_ID,
        keep=not args.no_keep,
        skip_break=args.skip_break,
    )
    print("\n".join(report.summary_lines()))
    return 0 if report.ok else 1


def _handle_export(args: argparse.Namespace) -> int:
    out = cmd_export(args.pack_id, output=args.output, root=args.root)
    print(f"Exported pack '{args.pack_id}' → {out}")
    return 0


def _handle_import(args: argparse.Namespace) -> int:
    pack = cmd_import(
        args.archive,
        root=args.root,
        force=args.force,
        rename=args.rename,
    )
    print(f"Imported pack '{pack.name}' → {pack}")
    return 0


def _handle_list(args: argparse.Namespace) -> int:
    rows = cmd_list(args.root)
    if not rows:
        print("No packs found under .failpack/packs/")
        return 0
    print("\n".join(format_table(rows)))
    return 0


def _handle_status(args: argparse.Namespace) -> int:
    report = cmd_status(args.pack_id, root=args.root)
    print("\n".join(report.summary_lines()))
    return 0


def _handle_show(args: argparse.Namespace) -> int:
    report = cmd_show(args.pack_id, root=args.root)
    if args.json:
        sys.stdout.write(report.to_json())
    else:
        print("\n".join(report.summary_lines()))
    return 0


def _handle_capture(args: argparse.Namespace) -> int:
    pack = cmd_capture(
        args.transcript,
        pack_id=args.pack_id,
        root=args.root,
        force=args.force,
        from_claude_project=args.from_claude_project,
        claude_latest=args.claude_latest,
        cursor_latest=args.cursor_latest,
        stdin=args.stdin,
        pattern=args.pattern,
    )
    print(f"Captured pack '{pack.name}' → {pack}")
    return 0


def _handle_promote(args: argparse.Namespace) -> int:
    suggest = bool(getattr(args, "suggest", False))
    write = bool(getattr(args, "write", False))
    dry_run = bool(args.dry_run)
    if write and not suggest and not dry_run:
        # --write alone is an explicit apply alias
        suggest = True
        write = True
    result = cmd_promote(
        args.pack_id,
        root=args.root,
        dry_run=dry_run,
        suggest=suggest,
        write=write,
    )
    if dry_run:
        assert isinstance(result, dict)
        print(f"# dry-run: would write assertions.yaml for '{args.pack_id}'")
        sys.stdout.write(format_assertions_preview(result))
        return 0
    if suggest and not write:
        assert isinstance(result, dict)
        sys.stdout.write(format_suggest_preview(result, pack_id=args.pack_id))
        return 0
    assert not isinstance(result, dict)
    print(f"Promoted pack '{result.name}' to golden ({result / 'assertions.yaml'})")
    return 0


def _handle_re_promote(args: argparse.Namespace) -> int:
    suggest = bool(getattr(args, "suggest", False))
    write = bool(getattr(args, "write", False))
    dry_run = bool(args.dry_run)
    if write and not suggest and not dry_run:
        suggest = True
        write = True
    result = cmd_re_promote(
        args.pack_id,
        root=args.root,
        dry_run=dry_run,
        suggest=suggest,
        write=write,
    )
    if dry_run:
        assert isinstance(result, dict)
        print(f"# dry-run: would re-write assertions.yaml for '{args.pack_id}'")
        sys.stdout.write(format_assertions_preview(result))
        return 0
    if suggest and not write:
        assert isinstance(result, dict)
        sys.stdout.write(format_suggest_preview(result, pack_id=args.pack_id))
        return 0
    assert not isinstance(result, dict)
    print(
        f"Re-promoted pack '{result.name}' — refreshed assertions from current artifacts "
        f"({result / 'assertions.yaml'})"
    )
    return 0


def _handle_watch(args: argparse.Namespace) -> int:
    pid, report = cmd_watch(
        args.transcript,
        pack_id=args.pack_id,
        root=args.root,
        force=args.force,
        from_claude_project=args.from_claude_project,
        claude_latest=args.claude_latest,
        cursor_latest=args.cursor_latest,
        stdin=args.stdin,
        pattern=args.pattern,
        show_diff=not args.no_diff,
    )
    print(f"Watched pack '{pid}' (capture → promote → replay)")
    print("\n".join(report.summary_lines()))
    return 0 if report.ok else 1


def _handle_replay(args: argparse.Namespace) -> int:
    show_diff = not args.no_diff
    if args.all and args.pack_id:
        raise ValueError("Use either a pack id or --all, not both.")
    if args.all:
        report = cmd_replay_all(root=args.root, show_diff=show_diff)
        if args.json:
            sys.stdout.write(report.to_json())
        else:
            print("\n".join(report.summary_lines()))
        return 0 if report.ok else 1
    if not args.pack_id:
        raise ValueError("Provide a pack id, or pass --all to replay every golden pack.")
    report = cmd_replay(args.pack_id, root=args.root, show_diff=show_diff)
    if args.json:
        sys.stdout.write(report.to_json())
    else:
        print("\n".join(report.summary_lines()))
    return 0 if report.ok else 1


def _handle_explain(args: argparse.Namespace) -> int:
    report = cmd_explain(args.pack_id, root=args.root)
    print("\n".join(report.summary_lines()))
    return 0 if report.ok else 1


def _handle_report(args: argparse.Namespace) -> int:
    if args.github and args.output is not None:
        raise ValueError("Use either --github or -o/--output, not both.")
    result = cmd_report(
        args.pack_id,
        root=args.root,
        github=args.github,
        output=args.output,
        show_diff=not args.no_diff,
    )
    if args.github or args.output is not None:
        print("\n".join(result.summary_lines()))
    else:
        sys.stdout.write(result.markdown)
        if not result.markdown.endswith("\n"):
            sys.stdout.write("\n")
    return 0 if result.ok else 1


def _handle_lint(args: argparse.Namespace) -> int:
    report = cmd_lint(args.pack_id, root=args.root)
    print("\n".join(report.summary_lines()))
    return 0 if report.ok else 1


def _handle_migrate(args: argparse.Namespace) -> int:
    report = cmd_migrate(root=args.root)
    print("\n".join(report.summary_lines()))
    return 0


def _handle_rm(args: argparse.Namespace) -> int:
    pack = cmd_rm(args.pack_id, root=args.root, force=args.force)
    print(f"Removed pack '{args.pack_id}' ({pack})")
    return 0


def _handle_rename(args: argparse.Namespace) -> int:
    pack = cmd_rename(args.old_id, args.new_id, root=args.root)
    print(f"Renamed pack '{args.old_id}' → '{args.new_id}' ({pack})")
    return 0


def _handle_completion(args: argparse.Namespace) -> int:
    sys.stdout.write(cmd_completion(args.shell))
    return 0


def _handle_license_check(args: argparse.Namespace) -> int:
    status = cmd_license_check()
    if status.ok:
        extra = []
        if status.plan:
            extra.append(f"plan={status.plan}")
        if status.subject:
            extra.append(f"sub={status.subject}")
        suffix = (" (" + ", ".join(extra) + ")") if extra else ""
        print(f"ok{suffix}")
        return 0
    print(f"fail: {status.message}")
    return 1


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = args.func(args)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        msg = str(exc)
        # Multi-line tips (e.g. capture with no args) print cleanly on stderr.
        if "\n" in msg:
            print(f"error: {msg.splitlines()[0]}", file=sys.stderr)
            for line in msg.splitlines()[1:]:
                print(line, file=sys.stderr)
        else:
            print(f"error: {msg}", file=sys.stderr)
        raise SystemExit(2) from exc
    raise SystemExit(code)


if __name__ == "__main__":
    main()
