"""Short unified diffs for explainable fingerprint failures."""

from __future__ import annotations

import difflib
from pathlib import Path

# Soft limits so FAIL output stays readable in terminals / CI logs.
MAX_FILE_CHARS = 32_768  # ~32 KiB per side before truncation marker
MAX_DIFF_LINES = 60


def is_probably_text(data: bytes) -> bool:
    """Heuristic: reject NUL bytes and empty/binary-looking blobs."""
    if not data:
        return True
    if b"\x00" in data:
        return False
    # Allow UTF-8 / latin-1-ish text; reject if too many control chars.
    sample = data[:8192]
    control = sum(1 for b in sample if b < 9 or (13 < b < 32) or b == 127)
    return control / max(len(sample), 1) < 0.05


def _truncate(text: str, limit: int = MAX_FILE_CHARS) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def read_text_for_diff(path: Path) -> str | None:
    """Read *path* as UTF-8 text for diffs, or None if missing/binary."""
    if not path.is_file():
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not is_probably_text(data):
        return None
    return data.decode("utf-8", errors="replace")


def short_unified_diff(
    expected: str,
    actual: str,
    *,
    fromfile: str = "expected",
    tofile: str = "actual",
    max_lines: int = MAX_DIFF_LINES,
) -> str:
    """Return a short unified diff; empty string if texts are identical."""
    exp, exp_cut = _truncate(expected)
    act, act_cut = _truncate(actual)
    if exp_cut:
        exp = exp + "\n… [truncated]\n"
    if act_cut:
        act = act + "\n… [truncated]\n"

    exp_lines = exp.splitlines(keepends=True)
    act_lines = act.splitlines(keepends=True)
    # Ensure trailing newline so difflib doesn't add "No newline" noise for snippets
    if exp_lines and not exp_lines[-1].endswith("\n"):
        exp_lines[-1] += "\n"
    if act_lines and not act_lines[-1].endswith("\n"):
        act_lines[-1] += "\n"

    diff_lines = list(
        difflib.unified_diff(
            exp_lines,
            act_lines,
            fromfile=fromfile,
            tofile=tofile,
            n=3,
        )
    )
    if not diff_lines:
        return ""

    if len(diff_lines) > max_lines:
        head = diff_lines[:max_lines]
        omitted = len(diff_lines) - max_lines
        head.append(f"… [{omitted} more diff lines truncated]\n")
        diff_lines = head

    return "".join(diff_lines).rstrip("\n")


def expected_snapshot_path(pack: Path, rel: str) -> Path:
    """Path under ``pack/expected/`` mirroring a fingerprinted relative path."""
    return pack / "expected" / rel


def write_expected_snapshot(pack: Path, rel: str, source: Path) -> bool:
    """Copy a text artifact into ``expected/`` for later diffs. Returns True if written."""
    if not source.is_file():
        return False
    try:
        data = source.read_bytes()
    except OSError:
        return False
    if not is_probably_text(data):
        return False
    # Skip huge binaries-as-text; still allow reasonably large logs.
    if len(data) > MAX_FILE_CHARS * 4:
        data = data[: MAX_FILE_CHARS * 4]
    dest = expected_snapshot_path(pack, rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


def fingerprint_diff(pack: Path, rel: str) -> str | None:
    """Unified diff of ``expected/<rel>`` vs current ``<rel>``, or None."""
    expected_path = expected_snapshot_path(pack, rel)
    actual_path = pack / rel
    expected = read_text_for_diff(expected_path)
    actual = read_text_for_diff(actual_path)
    if expected is None or actual is None:
        return None
    if expected == actual:
        return None
    return short_unified_diff(
        expected,
        actual,
        fromfile=f"expected/{rel}",
        tofile=rel,
    )
