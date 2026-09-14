"""Optional ANSI colors for CLI output (respects NO_COLOR / FORCE_COLOR)."""

from __future__ import annotations

import os
import sys


def use_color(*, stream: object | None = None) -> bool:
    """Return True when ANSI colors should be applied.

    Honors:
    - ``NO_COLOR`` (any value) → off
    - ``FORCE_COLOR`` (any value) → on
    - otherwise: on only when the stream is a TTY
    """
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    target = stream if stream is not None else sys.stdout
    return bool(getattr(target, "isatty", lambda: False)())


def paint(text: str, style: str, *, enabled: bool | None = None) -> str:
    if enabled is None:
        enabled = use_color()
    if not enabled:
        return text
    codes = {
        "green": "32",
        "red": "31",
        "yellow": "33",
        "bold": "1",
        "dim": "2",
    }
    code = codes.get(style)
    if not code:
        return text
    return f"\033[{code}m{text}\033[0m"
