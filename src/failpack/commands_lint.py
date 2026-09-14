"""failpack lint — light pack / assertion schema validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from failpack.assertions_schema import validate_assertions
from failpack.commands_list import list_packs
from failpack.pack import read_meta
from failpack.paths import (
    ASSERTIONS_NAME,
    ARTIFACTS_DIR,
    META_NAME,
    TRANSCRIPT_NAME,
    failpack_dir,
    packs_dir,
    require_pack,
)


@dataclass
class LintIssue:
    pack_id: str
    level: str  # "error" | "warning"
    message: str

    def format_line(self) -> str:
        return f"  [{self.level.upper()}] {self.pack_id}: {self.message}"


@dataclass
class LintReport:
    issues: list[LintIssue] = field(default_factory=list)
    checked: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    def summary_lines(self) -> list[str]:
        lines = ["failpack lint"]
        if not self.checked:
            lines.append("  (no packs found)")
            lines.append("RESULT: PASS")
            return lines
        for issue in self.issues:
            lines.append(issue.format_line())
        errors = sum(1 for i in self.issues if i.level == "error")
        warnings = sum(1 for i in self.issues if i.level == "warning")
        lines.append(
            f"SUMMARY: {len(self.checked)} pack(s) checked, "
            f"{errors} error(s), {warnings} warning(s)"
        )
        lines.append("RESULT: " + ("PASS" if self.ok else "FAIL"))
        return lines


def _lint_pack(pack: Path, pack_id: str) -> list[LintIssue]:
    issues: list[LintIssue] = []
    meta_path = pack / META_NAME
    if not meta_path.is_file():
        issues.append(LintIssue(pack_id, "error", f"missing {META_NAME}"))
        return issues

    try:
        meta: dict[str, Any] = read_meta(pack)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        issues.append(LintIssue(pack_id, "error", f"invalid {META_NAME}: {exc}"))
        return issues

    meta_id = meta.get("id")
    if meta_id is None:
        issues.append(LintIssue(pack_id, "error", "meta.id missing"))
    elif str(meta_id) != pack.name:
        issues.append(
            LintIssue(
                pack_id,
                "error",
                f"meta.id {meta_id!r} does not match directory name {pack.name!r}",
            )
        )

    status = meta.get("status")
    if status not in {"captured", "golden"}:
        issues.append(
            LintIssue(
                pack_id,
                "warning",
                f"unexpected status {status!r} (expected captured|golden)",
            )
        )

    if "schema_version" not in meta:
        issues.append(
            LintIssue(
                pack_id,
                "warning",
                "meta.schema_version unset — run `failpack migrate`",
            )
        )

    if not (pack / TRANSCRIPT_NAME).is_file():
        issues.append(LintIssue(pack_id, "warning", f"missing {TRANSCRIPT_NAME}"))

    arts = pack / ARTIFACTS_DIR
    if not arts.is_dir():
        issues.append(LintIssue(pack_id, "error", f"missing {ARTIFACTS_DIR}/"))
    else:
        for required in ("exit_code.txt", "status.txt", "error.txt"):
            if not (arts / required).is_file():
                issues.append(
                    LintIssue(pack_id, "warning", f"missing artifacts/{required}")
                )

    assertions_path = pack / ASSERTIONS_NAME
    if status == "golden" and not assertions_path.is_file():
        issues.append(
            LintIssue(
                pack_id,
                "error",
                f"golden pack missing {ASSERTIONS_NAME} — run `failpack promote {pack_id}`",
            )
        )
    elif assertions_path.is_file():
        try:
            raw = yaml.safe_load(assertions_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            issues.append(
                LintIssue(pack_id, "error", f"invalid {ASSERTIONS_NAME}: {exc}")
            )
            return issues
        if not isinstance(raw, dict):
            issues.append(
                LintIssue(pack_id, "error", f"{ASSERTIONS_NAME} must be a mapping")
            )
            return issues
        try:
            validate_assertions(raw)
        except ValueError as exc:
            issues.append(
                LintIssue(pack_id, "error", f"assertion schema: {exc}")
            )
        else:
            aid = raw.get("pack_id")
            if aid is not None and str(aid) != pack.name:
                issues.append(
                    LintIssue(
                        pack_id,
                        "warning",
                        f"assertions pack_id {aid!r} does not match directory "
                        f"name {pack.name!r}",
                    )
                )

    return issues


def cmd_lint(
    pack_id: str | None = None,
    *,
    root: Path | None = None,
) -> LintReport:
    """Validate pack layout + assertion schema (no replay)."""
    report = LintReport()
    base = failpack_dir(root)
    if not base.is_dir():
        raise FileNotFoundError(
            f"No {base.name}/ directory. Run `failpack init` first."
        )

    if pack_id:
        pack = require_pack(pack_id, root)
        report.checked.append(pack_id)
        report.issues.extend(_lint_pack(pack, pack_id))
        return report

    packs = packs_dir(root)
    if not packs.is_dir():
        return report

    # Prefer list_packs order (meta.json present); also catch dirs without meta
    seen: set[str] = set()
    for row in list_packs(root):
        seen.add(row.id)
        path = packs / row.id
        report.checked.append(row.id)
        report.issues.extend(_lint_pack(path, row.id))

    for path in sorted(packs.iterdir()):
        if not path.is_dir() or path.name.startswith("."):
            continue
        if path.name in seen:
            continue
        report.checked.append(path.name)
        report.issues.extend(_lint_pack(path, path.name))

    return report
