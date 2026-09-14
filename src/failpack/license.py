"""License token stub for future Pro gating.

Token format (v1)::

    v1.<base64url(json_payload)>.<base64url(hmac_sha256)>

Payload JSON keys: ``plan`` (personal|team), optional ``sub``, optional ``exp`` (unix).

Environment:

- ``FAILPACK_LICENSE`` — the signed token
- ``FAILPACK_LICENSE_SECRET`` — HMAC key (defaults to a documented stub for local demos)

This module does **not** call any network API. Pro features (private pack sync,
dashboard) will gate on ``check_license()`` later; open CLI commands stay free.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

# Dev-only default so `failpack license check` is demonstrable offline.
# Production issuers must set FAILPACK_LICENSE_SECRET to a real key.
STUB_SECRET = "failpack-dev-stub-secret-not-for-production"

ENV_LICENSE = "FAILPACK_LICENSE"
ENV_SECRET = "FAILPACK_LICENSE_SECRET"


@dataclass(frozen=True)
class LicenseStatus:
    ok: bool
    message: str
    plan: str | None = None
    subject: str | None = None


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _secret() -> bytes:
    return os.environ.get(ENV_SECRET, STUB_SECRET).encode("utf-8")


def mint_token(
    *,
    plan: str = "personal",
    subject: str | None = None,
    exp: int | None = None,
    secret: bytes | None = None,
) -> str:
    """Mint a v1 token (test / local issuer helper)."""
    payload: dict[str, Any] = {"plan": plan}
    if subject:
        payload["sub"] = subject
    if exp is not None:
        payload["exp"] = int(exp)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    key = secret if secret is not None else _secret()
    sig = hmac.new(key, body, hashlib.sha256).digest()
    return f"v1.{_b64url_encode(body)}.{_b64url_encode(sig)}"


def verify_token(token: str, *, now: int | None = None) -> LicenseStatus:
    token = token.strip()
    if not token:
        return LicenseStatus(False, "empty license token")

    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        return LicenseStatus(False, "invalid token format (expected v1.<payload>.<sig>)")

    try:
        body = _b64url_decode(parts[1])
        sig = _b64url_decode(parts[2])
    except Exception:
        return LicenseStatus(False, "token is not valid base64url")

    expected = hmac.new(_secret(), body, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return LicenseStatus(False, "signature mismatch (bad token or secret)")

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return LicenseStatus(False, "payload is not valid JSON")

    if not isinstance(payload, dict):
        return LicenseStatus(False, "payload must be a JSON object")

    plan = payload.get("plan")
    if plan not in ("personal", "team"):
        return LicenseStatus(False, f"unknown plan: {plan!r}")

    exp = payload.get("exp")
    if exp is not None:
        try:
            exp_i = int(exp)
        except (TypeError, ValueError):
            return LicenseStatus(False, "exp must be a unix timestamp")
        ts = int(time.time() if now is None else now)
        if ts > exp_i:
            return LicenseStatus(False, "license expired", plan=str(plan))

    sub = payload.get("sub")
    return LicenseStatus(
        True,
        "ok",
        plan=str(plan),
        subject=str(sub) if sub is not None else None,
    )


def check_license_env(*, environ: dict[str, str] | None = None) -> LicenseStatus:
    env = environ if environ is not None else os.environ
    raw = env.get(ENV_LICENSE, "").strip()
    if not raw:
        return LicenseStatus(
            False,
            f"{ENV_LICENSE} is not set — open CLI stays free; Pro features will require a license",
        )
    # verify_token reads secret from os.environ; temporarily align if custom environ
    if environ is not None:
        prev_secret = os.environ.get(ENV_SECRET)
        try:
            if ENV_SECRET in environ:
                os.environ[ENV_SECRET] = environ[ENV_SECRET]
            elif ENV_SECRET in os.environ:
                del os.environ[ENV_SECRET]
            return verify_token(raw)
        finally:
            if prev_secret is None:
                os.environ.pop(ENV_SECRET, None)
            else:
                os.environ[ENV_SECRET] = prev_secret
    return verify_token(raw)


def cmd_license_check() -> LicenseStatus:
    return check_license_env()
