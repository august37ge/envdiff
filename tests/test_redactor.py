"""Tests for envdiff.redactor."""

from __future__ import annotations

import pytest

from envdiff.redactor import (
    REDACTED_PLACEHOLDER,
    RedactError,
    RedactOptions,
    redact,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# RedactOptions validation
# ---------------------------------------------------------------------------

def test_invalid_pattern_raises():
    with pytest.raises(RedactError, match="Invalid redact pattern"):
        RedactOptions(patterns=["[unclosed"])


def test_default_options_compile_without_error():
    opts = RedactOptions()
    assert len(opts.patterns) >= 1


# ---------------------------------------------------------------------------
# redact() core behaviour
# ---------------------------------------------------------------------------

def test_non_sensitive_key_unchanged():
    env = _env(APP_NAME="myapp", DEBUG="true")
    result = redact(env)
    assert result["APP_NAME"] == "myapp"
    assert result["DEBUG"] == "true"


def test_password_key_is_redacted():
    env = _env(DB_PASSWORD="s3cr3t")
    result = redact(env)
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER


def test_token_key_is_redacted():
    env = _env(GITHUB_TOKEN="ghp_abc123")
    result = redact(env)
    assert result["GITHUB_TOKEN"] == REDACTED_PLACEHOLDER


def test_api_key_is_redacted():
    env = _env(STRIPE_API_KEY="sk_live_xyz")
    result = redact(env)
    assert result["STRIPE_API_KEY"] == REDACTED_PLACEHOLDER


def test_secret_key_is_redacted():
    env = _env(SECRET_KEY="supersecret")
    result = redact(env)
    assert result["SECRET_KEY"] == REDACTED_PLACEHOLDER


def test_original_dict_not_mutated():
    env = _env(DB_PASSWORD="s3cr3t", APP_NAME="myapp")
    original = dict(env)
    redact(env)
    assert env == original


def test_extra_keys_option_redacts_arbitrary_key():
    env = _env(MY_CUSTOM_FIELD="value", OTHER="ok")
    opts = RedactOptions(extra_keys=["MY_CUSTOM_FIELD"])
    result = redact(env, opts)
    assert result["MY_CUSTOM_FIELD"] == REDACTED_PLACEHOLDER
    assert result["OTHER"] == "ok"


def test_custom_placeholder():
    env = _env(DB_PASSWORD="s3cr3t")
    opts = RedactOptions(placeholder="<hidden>")
    result = redact(env, opts)
    assert result["DB_PASSWORD"] == "<hidden>"


def test_empty_env_returns_empty():
    assert redact({}) == {}


def test_case_insensitive_match():
    env = _env(db_password="lowercase_secret")
    result = redact(env)
    assert result["db_password"] == REDACTED_PLACEHOLDER
