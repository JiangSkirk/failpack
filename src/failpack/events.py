"""Scan Claude-Code-like transcript events for assertion helpers."""

from __future__ import annotations

import re
from typing import Any

from failpack.transcript import _text_from_content, load_jsonl

_DENY_RE = re.compile(
    r"\b(denied|deny|permission\s+denied|not\s+allowed|blocked|rejected)\b",
    re.I,
)


def _tool_name_from_block(block: dict[str, Any]) -> str | None:
    name = block.get("name") or block.get("tool")
    return str(name) if name else None


def iter_tool_uses(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ``{id, name, input}`` for each tool_use / tool_call in the session."""
    uses: list[dict[str, Any]] = []
    for ev in events:
        etype = ev.get("type") or ev.get("role") or ""
        if etype in ("assistant", "ai"):
            msg = ev.get("message") or ev
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") in ("tool_use", "tool_call"):
                        uses.append(
                            {
                                "id": block.get("id") or block.get("tool_use_id"),
                                "name": _tool_name_from_block(block) or "",
                                "input": block.get("input") or block.get("arguments") or {},
                            }
                        )
            if "tool_use" in ev and isinstance(ev["tool_use"], dict):
                tu = ev["tool_use"]
                uses.append(
                    {
                        "id": tu.get("id") or tu.get("tool_use_id"),
                        "name": _tool_name_from_block(tu) or "",
                        "input": tu.get("input") or {},
                    }
                )
    return uses


def denied_tool_names(events: list[dict[str, Any]]) -> list[str]:
    """Tool names that appear denied / blocked in the transcript.

    Matches (only names that appear as tool_use in the session):
    - ``tool_result`` with ``denied`` / deny-ish error text linked to a tool_use
    - free-text like ``Tool use denied: Bash`` when Bash was a tool_use
    """
    uses = iter_tool_uses(events)
    by_id = {u["id"]: u["name"] for u in uses if u.get("id")}
    known = {str(u.get("name") or "") for u in uses if u.get("name")}
    known_lower = {n.lower(): n for n in known}
    denied: list[str] = []
    seen: set[str] = set()

    def _add(name: str | None) -> None:
        if not name:
            return
        # Prefer the canonical casing from tool_use when possible
        canonical = known_lower.get(name.lower(), name)
        if canonical not in known and name not in known:
            # Only accept names that were actually invoked in this session
            return
        key = canonical.lower()
        if key in seen:
            return
        seen.add(key)
        denied.append(canonical)

    for ev in events:
        etype = ev.get("type") or ev.get("role") or ""
        raw_msg = ev.get("content") or ev.get("result") or ev.get("message") or ""
        if isinstance(raw_msg, dict):
            text = _text_from_content(raw_msg.get("content") if "content" in raw_msg else raw_msg)
        else:
            text = _text_from_content(raw_msg)

        if etype in ("tool_result", "tool"):
            tool_id = ev.get("tool_use_id") or ev.get("tool_useId") or ev.get("id")
            name = by_id.get(tool_id) if tool_id else None
            looks_denied = bool(_DENY_RE.search(text))
            if ev.get("denied") or ev.get("permission") in ("deny", "denied", "rejected"):
                looks_denied = True
            if name and (looks_denied or ev.get("denied") or (ev.get("is_error") and looks_denied)):
                _add(name)
            if looks_denied:
                for n in known:
                    if re.search(rf"\b{re.escape(n)}\b", text):
                        _add(n)

        # Prose mentioning a denied tool (assistant / result / etc.)
        if text and _DENY_RE.search(text):
            for n in known:
                if re.search(
                    rf"(denied|deny|blocked|rejected).{{0,48}}\b{re.escape(n)}\b"
                    rf"|\b{re.escape(n)}\b.{{0,48}}(denied|deny|blocked|rejected)",
                    text,
                    re.I,
                ):
                    _add(n)

            # Patterns like: Tool use denied: Bash / denied tool: Write
            for m in re.finditer(
                r"(?:tool(?:\s+use)?\s+)denied[:\s]+([A-Za-z_][\w.-]*)"
                r"|denied\s+tool[:\s]+([A-Za-z_][\w.-]*)",
                text,
                re.I,
            ):
                _add(next(g for g in m.groups() if g))

    return denied


def bash_outputs(events: list[dict[str, Any]]) -> list[str]:
    """Return Bash / bash / Shell tool_result texts in session order."""
    uses = iter_tool_uses(events)
    bash_ids = {
        u["id"]
        for u in uses
        if u.get("id") and str(u.get("name") or "").lower() in {"bash", "shell", "terminal"}
    }
    # Also accept tool_use without id by pairing in order (fallback)
    outputs: list[str] = []
    for ev in events:
        etype = ev.get("type") or ev.get("role") or ""
        if etype not in ("tool_result", "tool"):
            continue
        tool_id = ev.get("tool_use_id") or ev.get("tool_useId") or ev.get("id")
        if bash_ids and tool_id not in bash_ids:
            continue
        if not bash_ids:
            # No bash tool_use ids recorded — skip unless content looks shell-ish
            # and we have no uses at all matching bash
            continue
        text = _text_from_content(ev.get("content") or ev.get("result") or "")
        outputs.append(text)
    return outputs


def tool_denied_contains(events: list[dict[str, Any]], needle: str) -> bool:
    """True if any denied tool name contains *needle* (case-sensitive substring)."""
    if not needle:
        return False
    return any(needle in name for name in denied_tool_names(events))


def bash_output_contains(
    events: list[dict[str, Any]],
    needle: str,
    *,
    match: str = "any",
) -> bool:
    """True if Bash tool output contains *needle*.

    *match*:
    - ``any`` (default) — any Bash tool_result contains the needle
    - ``last`` — only the last Bash tool_result
    """
    if not needle:
        return False
    outs = bash_outputs(events)
    if not outs:
        return False
    mode = (match or "any").lower()
    if mode == "last":
        return needle in outs[-1]
    return any(needle in o for o in outs)


def load_pack_events(transcript_path: Any) -> list[dict[str, Any]]:
    """Load JSONL events from a pack transcript path."""
    return load_jsonl(transcript_path)
