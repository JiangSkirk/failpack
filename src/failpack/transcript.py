"""Parse Claude-Code-like JSONL transcripts into pack artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{lineno}: invalid JSON — {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{lineno}: expected JSON object")
        events.append(obj)
    if not events:
        raise ValueError(f"{path}: empty transcript")
    return events


def _text_from_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block["text"]))
        return "\n".join(p for p in parts if p)
    if isinstance(content, dict):
        return str(content.get("text") or content.get("content") or "")
    return str(content)


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract a compact failure summary from a Claude-Code-like session."""
    user_prompts: list[str] = []
    assistant_texts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    written_files: dict[str, str] = {}
    exit_code: int | None = None
    error_message: str | None = None
    session_id: str | None = None
    status = "unknown"

    for ev in events:
        etype = ev.get("type") or ev.get("role") or ""
        session_id = session_id or ev.get("session_id") or ev.get("sessionId")

        if etype in ("user", "human"):
            msg = ev.get("message") or ev
            text = _text_from_content(msg.get("content") if isinstance(msg, dict) else msg)
            if text:
                user_prompts.append(text)

        elif etype in ("assistant", "ai"):
            msg = ev.get("message") or ev
            if isinstance(msg, dict):
                content = msg.get("content")
                text = _text_from_content(content)
                if text:
                    assistant_texts.append(text)
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") in ("tool_use", "tool_call"):
                            name = block.get("name") or block.get("tool")
                            inp = block.get("input") or block.get("arguments") or {}
                            tool_calls.append({"name": name, "input": inp})
                            if name in ("Write", "write_file", "create_file") and isinstance(inp, dict):
                                path = inp.get("file_path") or inp.get("path") or inp.get("filename")
                                body = inp.get("content") or inp.get("contents") or ""
                                if path:
                                    written_files[str(path)] = str(body)
            if "tool_use" in ev and isinstance(ev["tool_use"], dict):
                tu = ev["tool_use"]
                tool_calls.append({"name": tu.get("name"), "input": tu.get("input") or {}})

        elif etype in ("tool_result", "tool"):
            content = ev.get("content") or ev.get("result") or ""
            text = _text_from_content(content)
            if ev.get("is_error") or ev.get("is_error") is True:
                error_message = error_message or text
            m = re.search(r"exit[_ ]?code[=:\s]+(-?\d+)", text, re.I)
            if m:
                exit_code = int(m.group(1))

        elif etype in ("result", "session_result", "final"):
            if "exit_code" in ev:
                exit_code = int(ev["exit_code"])
            elif "exitCode" in ev:
                exit_code = int(ev["exitCode"])
            if ev.get("is_error") or ev.get("subtype") in ("error", "failure"):
                status = "failed"
                err = ev.get("result") or ev.get("error") or ev.get("message")
                if err:
                    error_message = _text_from_content(err)
            elif ev.get("subtype") in ("success", "completed"):
                status = "ok"
            if "result" in ev and status == "unknown":
                result_text = _text_from_content(ev.get("result"))
                if re.search(r"\b(error|failed|traceback|exception)\b", result_text, re.I):
                    status = "failed"
                    error_message = error_message or result_text
                elif result_text:
                    status = "ok"

        if etype == "error":
            status = "failed"
            error_message = error_message or _text_from_content(ev.get("message") or ev.get("error"))

    if exit_code is None:
        exit_code = 1 if status == "failed" else 0
    if status == "unknown":
        status = "failed" if exit_code != 0 else "ok"

    return {
        "session_id": session_id,
        "status": status,
        "exit_code": exit_code,
        "error_message": error_message or "",
        "user_prompts": user_prompts,
        "assistant_texts": assistant_texts,
        "tool_calls": tool_calls,
        "written_files": written_files,
        "event_count": len(events),
    }


def write_artifacts(artifacts: Path, summary: dict[str, Any]) -> None:
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "exit_code.txt").write_text(str(summary["exit_code"]) + "\n", encoding="utf-8")
    (artifacts / "status.txt").write_text(summary["status"] + "\n", encoding="utf-8")
    (artifacts / "error.txt").write_text(summary.get("error_message") or "", encoding="utf-8")

    files_dir = artifacts / "files"
    if summary.get("written_files"):
        files_dir.mkdir(parents=True, exist_ok=True)
        for rel, body in summary["written_files"].items():
            safe = Path(rel)
            parts = [p for p in safe.parts if p not in ("/", "\\") and not (len(p) == 2 and p.endswith(":"))]
            target = files_dir.joinpath(*parts) if parts else files_dir / "unnamed"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

    summary_md = _render_summary_md(summary)
    (artifacts / "summary.md").write_text(summary_md, encoding="utf-8")

    digest = {
        "exit_code": summary["exit_code"],
        "status": summary["status"],
        "error_message": summary.get("error_message") or "",
        "written_files": sorted(summary.get("written_files", {}).keys()),
        "event_count": summary["event_count"],
    }
    (artifacts / "digest.json").write_text(
        json.dumps(digest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _render_summary_md(summary: dict[str, Any]) -> str:
    prompts = summary.get("user_prompts") or []
    first_prompt = prompts[0] if prompts else "(none)"
    files = summary.get("written_files") or {}
    file_lines = "\n".join(f"- `{p}`" for p in files) or "- (none)"
    err = summary.get("error_message") or "(none)"
    return (
        f"# Session summary\n\n"
        f"- **status**: `{summary['status']}`\n"
        f"- **exit_code**: `{summary['exit_code']}`\n"
        f"- **events**: `{summary['event_count']}`\n\n"
        f"## User prompt\n\n{first_prompt}\n\n"
        f"## Error\n\n```\n{err}\n```\n\n"
        f"## Written files\n\n{file_lines}\n"
    )


def slug_from_summary(summary: dict[str, Any], source: Path) -> str:
    """Pick a short pack id from summary / filename."""
    if summary.get("session_id"):
        sid = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(summary["session_id"])).strip("-").lower()
        if sid:
            return sid[:48]
    stem = source.stem.lower()
    stem = re.sub(r"[^a-z0-9_-]+", "-", stem).strip("-")
    return stem[:48] or "pack"
