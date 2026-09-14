"""Tests for failpack license check stub."""

from __future__ import annotations

import os

import pytest

from failpack.license import (
    ENV_LICENSE,
    ENV_SECRET,
    check_license_env,
    mint_token,
    verify_token,
)


def test_missing_license_fails() -> None:
    status = check_license_env(environ={})
    assert not status.ok
    assert ENV_LICENSE in status.message


def test_valid_personal_token_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_SECRET, raising=False)
    token = mint_token(plan="personal", subject="dev@example.com")
    monkeypatch.setenv(ENV_LICENSE, token)
    status = check_license_env()
    assert status.ok
    assert status.plan == "personal"
    assert status.subject == "dev@example.com"


def test_tampered_token_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_SECRET, raising=False)
    token = mint_token(plan="team")
    # flip a character in the signature segment
    parts = token.split(".")
    sig = parts[2]
    flipped = ("A" if sig[0] != "A" else "B") + sig[1:]
    bad = ".".join([parts[0], parts[1], flipped])
    status = verify_token(bad)
    assert not status.ok
    assert "signature" in status.message.lower()


def test_expired_token_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_SECRET, raising=False)
    token = mint_token(plan="personal", exp=1_700_000_000)  # past
    status = verify_token(token, now=1_800_000_000)
    assert not status.ok
    assert "expired" in status.message.lower()


def test_custom_secret_must_match(monkeypatch: pytest.MonkeyPatch) -> None:
    token = mint_token(plan="personal", secret=b"prod-secret")
    monkeypatch.setenv(ENV_SECRET, "prod-secret")
    monkeypatch.setenv(ENV_LICENSE, token)
    assert check_license_env().ok
    monkeypatch.setenv(ENV_SECRET, "other-secret")
    assert not check_license_env().ok


def test_cli_license_check_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    from failpack.cli import main

    monkeypatch.delenv(ENV_SECRET, raising=False)
    token = mint_token(plan="team", subject="ops@acme.test")
    monkeypatch.setenv(ENV_LICENSE, token)
    with pytest.raises(SystemExit) as exc:
        main(["license", "check"])
    assert exc.value.code == 0


def test_cli_license_check_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    from failpack.cli import main

    monkeypatch.delenv(ENV_LICENSE, raising=False)
    with pytest.raises(SystemExit) as exc:
        main(["license", "check"])
    assert exc.value.code == 1
