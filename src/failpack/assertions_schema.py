"""Assertion schema validation — known kinds + required fields."""

from __future__ import annotations

from typing import Any

# Top-level bookkeeping keys (not assertion kinds).
ASSERTION_META_KEYS = frozenset({"version", "pack_id", "description"})

# Known assertion kinds (top-level keys that define checks).
KNOWN_ASSERTION_KINDS = frozenset(
    {
        "exit_code",
        "fingerprints",
        "substrings",
        "min_events",
        "glob_fingerprint",
        "glob_fingerprints",
        "tool_denied_contains",
        "bash_output_contains",
    }
)

_KNOWN_SORTED = ", ".join(sorted(KNOWN_ASSERTION_KINDS))


def _normalize_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    return [raw]


def _require_fields(
    kind: str,
    entry: dict[str, Any],
    fields: tuple[str, ...],
    *,
    index: int | None = None,
) -> None:
    missing = [f for f in fields if not entry.get(f)]
    # Allow alternate field names where documented
    if "pattern" in fields and missing and "pattern" in missing and entry.get("glob"):
        missing = [f for f in missing if f != "pattern"]
    if missing:
        where = f"{kind}[{index}]" if index is not None else kind
        raise ValueError(
            f"Assertion {where} missing required field(s): {', '.join(missing)}"
        )


def validate_assertions(data: dict[str, Any]) -> dict[str, Any]:
    """Validate assertions.yaml structure.

    Raises ``ValueError`` with a crisp message for unknown kinds or missing
    required fields. Does not silently ignore incomplete entries.
    """
    if not isinstance(data, dict):
        raise ValueError("assertions must be a mapping")

    for key in data:
        if key in ASSERTION_META_KEYS:
            continue
        if key not in KNOWN_ASSERTION_KINDS:
            raise ValueError(
                f"Unknown assertion kind {key!r}. "
                f"Known kinds: {_KNOWN_SORTED}"
            )

    if "exit_code" in data and data["exit_code"] is not None:
        try:
            int(data["exit_code"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Assertion kind 'exit_code' must be an integer, got {data['exit_code']!r}"
            ) from exc

    if "min_events" in data and data["min_events"] is not None:
        try:
            int(data["min_events"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Assertion kind 'min_events' must be an integer, got {data['min_events']!r}"
            ) from exc

    for i, fp in enumerate(_normalize_list(data.get("fingerprints"))):
        if not isinstance(fp, dict):
            raise ValueError(
                f"Assertion fingerprints[{i}] must be a mapping with path + sha256"
            )
        _require_fields("fingerprints", fp, ("path", "sha256"), index=i)

    for i, sub in enumerate(_normalize_list(data.get("substrings"))):
        if not isinstance(sub, dict):
            raise ValueError(
                f"Assertion substrings[{i}] must be a mapping with path + contains"
            )
        _require_fields("substrings", sub, ("path", "contains"), index=i)

    for key in ("glob_fingerprint", "glob_fingerprints"):
        if key not in data:
            continue
        for i, entry in enumerate(_normalize_list(data[key])):
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Assertion {key}[{i}] must be a mapping with pattern + sha256"
                )
            missing = []
            if not (entry.get("pattern") or entry.get("glob")):
                missing.append("pattern")
            if not entry.get("sha256"):
                missing.append("sha256")
            if missing:
                raise ValueError(
                    f"Assertion {key}[{i}] missing required field(s): {', '.join(missing)}"
                )

    for kind in ("tool_denied_contains", "bash_output_contains"):
        if kind not in data:
            continue
        raw = data[kind]
        entries: list[Any]
        if isinstance(raw, str):
            entries = [{"contains": raw}]
        else:
            entries = _normalize_list(raw)
        for i, entry in enumerate(entries):
            if isinstance(entry, str):
                continue
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Assertion {kind}[{i}] must be a string or mapping with contains"
                )
            if not entry.get("contains"):
                raise ValueError(
                    f"Assertion {kind}[{i}] missing required field(s): contains"
                )
            if kind == "bash_output_contains":
                match = entry.get("match") or entry.get("which")
                if match is not None and str(match) not in {"any", "last"}:
                    raise ValueError(
                        f"Assertion {kind}[{i}] has invalid match {match!r} "
                        "(expected 'any' or 'last')"
                    )

    return data
