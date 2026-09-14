"""FailPack CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from failpack import __version__
from failpack.commands_capture import cmd_capture
from failpack.commands_doctor import cmd_doctor
from failpack.commands_init import cmd_init
from failpack.commands_list import cmd_list
from failpack.commands_migrate import cmd_migrate
from failpack.commands_promote import cmd_promote
from failpack.commands_replay import cmd_replay, cmd_replay_all
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
            "  failpack doctor\n"
            "  failpack capture fixtures/claude-code-failure.jsonl --id my-failure\n"
            "  failpack promote my-failure\n"
            "  failpack replay my-failure\n"
            "  failpack replay --all\n"
            "  failpack watch fixtures/claude-code-failure.jsonl --id my-failure\n"
            "  failpack migrate\n"
            "  failpack init --ci\n"
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
        help="Check Python, PyYAML, .failpack/ layout, and pack counts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  failpack doctor\n",
    )
    p_doctor.set_defaults(func=_handle_doctor)

    p_list = sub.add_parser(
        "list",
        help="List packs under .failpack/packs/",
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

    p_cap = sub.add_parser(
        "capture",
        help="Ingest a Claude-Code-like JSONL transcript",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack capture fixtures/claude-code-failure.jsonl --id my-failure\n"
            "  failpack capture ~/.claude/projects --id my-failure\n"
            "  failpack capture --from-claude-project ~/.claude/projects\n"
            "  failpack capture --stdin < session.jsonl\n"
            "  failpack capture 'fixtures/*.jsonl' --id from-glob\n"
            "\n"
            "tip: a directory argument picks the newest *.jsonl underneath\n"
            "(Claude Code sessions are often under ~/.claude/projects).\n"
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
        epilog="examples:\n  failpack promote my-failure\n",
    )
    p_prom.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_prom.set_defaults(func=_handle_promote)

    p_watch = sub.add_parser(
        "watch",
        help="Capture → promote → replay (local pre-commit / docs helper)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  failpack watch fixtures/claude-code-failure.jsonl --id my-failure\n"
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
            "(e.g. re-promote after intentional change / artifact drifted — inspect path).\n"
            "Fingerprint failures also show a short unified diff of expected vs actual\n"
            "artifact text when a promote-time snapshot exists (disable with --no-diff).\n"
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

    p_mig = sub.add_parser(
        "migrate",
        help="Stamp pack schema_version (no-op if already current)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  failpack migrate\n",
    )
    p_mig.set_defaults(func=_handle_migrate)

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
    report = cmd_doctor(args.root)
    print("\n".join(report.summary_lines()))
    return 0 if report.ok else 1


def _handle_list(args: argparse.Namespace) -> int:
    rows = cmd_list(args.root)
    if not rows:
        print("No packs found under .failpack/packs/")
        return 0
    print("ID\tSTATUS\tEXIT\tPROMOTED_AT")
    for row in rows:
        print(row.format_line())
    return 0


def _handle_status(args: argparse.Namespace) -> int:
    report = cmd_status(args.pack_id, root=args.root)
    print("\n".join(report.summary_lines()))
    return 0


def _handle_capture(args: argparse.Namespace) -> int:
    pack = cmd_capture(
        args.transcript,
        pack_id=args.pack_id,
        root=args.root,
        force=args.force,
        from_claude_project=args.from_claude_project,
        stdin=args.stdin,
        pattern=args.pattern,
    )
    print(f"Captured pack '{pack.name}' → {pack}")
    return 0


def _handle_promote(args: argparse.Namespace) -> int:
    pack = cmd_promote(args.pack_id, root=args.root)
    print(f"Promoted pack '{pack.name}' to golden ({pack / 'assertions.yaml'})")
    return 0


def _handle_watch(args: argparse.Namespace) -> int:
    pid, report = cmd_watch(
        args.transcript,
        pack_id=args.pack_id,
        root=args.root,
        force=args.force,
        from_claude_project=args.from_claude_project,
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


def _handle_migrate(args: argparse.Namespace) -> int:
    report = cmd_migrate(root=args.root)
    print("\n".join(report.summary_lines()))
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
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    raise SystemExit(code)


if __name__ == "__main__":
    main()
