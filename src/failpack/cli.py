"""FailPack CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from failpack import __version__
from failpack.commands_capture import cmd_capture
from failpack.commands_init import cmd_init
from failpack.commands_promote import cmd_promote
from failpack.commands_replay import cmd_replay
from failpack.license import cmd_license_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="failpack",
        description=(
            "FailPack (Orin Replay): turn coding-agent failure sessions "
            "into golden CI regression packs."
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

    p_init = sub.add_parser("init", help="Create .failpack/ workspace layout")
    p_init.set_defaults(func=_handle_init)

    p_cap = sub.add_parser("capture", help="Ingest a Claude-Code-like JSONL transcript")
    p_cap.add_argument("transcript", type=Path, help="Path to transcript.jsonl")
    p_cap.add_argument("--id", dest="pack_id", default=None, help="Pack id (default: from transcript)")
    p_cap.add_argument("--force", action="store_true", help="Overwrite existing pack")
    p_cap.set_defaults(func=_handle_capture)

    p_prom = sub.add_parser("promote", help="Mark pack golden and write assertions.yaml")
    p_prom.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_prom.set_defaults(func=_handle_promote)

    p_rep = sub.add_parser("replay", help="Verify golden assertions (exit 0 pass / non-zero fail)")
    p_rep.add_argument("pack_id", help="Pack id under .failpack/packs/")
    p_rep.set_defaults(func=_handle_replay)

    p_lic = sub.add_parser("license", help="License helpers for future Pro gating")
    lic_sub = p_lic.add_subparsers(dest="license_cmd", required=True)
    p_lic_check = lic_sub.add_parser("check", help="Validate FAILPACK_LICENSE (HMAC stub)")
    p_lic_check.set_defaults(func=_handle_license_check)

    return parser


def _handle_init(args: argparse.Namespace) -> int:
    path = cmd_init(args.root)
    print(f"Initialized FailPack workspace at {path}")
    return 0


def _handle_capture(args: argparse.Namespace) -> int:
    pack = cmd_capture(
        args.transcript,
        pack_id=args.pack_id,
        root=args.root,
        force=args.force,
    )
    print(f"Captured pack '{pack.name}' → {pack}")
    return 0


def _handle_promote(args: argparse.Namespace) -> int:
    pack = cmd_promote(args.pack_id, root=args.root)
    print(f"Promoted pack '{pack.name}' to golden ({pack / 'assertions.yaml'})")
    return 0


def _handle_replay(args: argparse.Namespace) -> int:
    report = cmd_replay(args.pack_id, root=args.root)
    print("\n".join(report.summary_lines()))
    return 0 if report.ok else 1



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
