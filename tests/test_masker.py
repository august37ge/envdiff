"""Tests for envdiff.masker."""
from __future__ import annotations

import pytest

from envdiff.masker import MaskError, MaskOptions, MaskResult, mask_env, MASK_PLACEHOLDER


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# MaskOptions
# ---------------------------------------------------------------------------

def test_default_options_compile_without_error():
    opts = MaskOptions()
    assert opts._compiled  # at least one compiled pattern


def test_invalid_pattern_raises():
    with pytest.raises(MaskError, match="Invalid mask pattern"):
        MaskOptions(patterns=["[invalid"])


def test_should_mask_password_key():
    opts = MaskOptions()
    assert opts.should_mask("DB_PASSWORD") is True


def test_should_mask_token_key():
    opts = MaskOptions()
    assert opts.should_mask("GITHUB_TOKEN") is True


def test_should_not_mask_plain_key():
    opts = MaskOptions()
    assert opts.should_mask("APP_ENV") is False


def test_extra_keys_are_masked():
    opts = MaskOptions(extra_keys=["MY_CUSTOM_KEY"])
    assert opts.should_mask("MY_CUSTOM_KEY") is True


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

def test_none_env_raises():
    with pytest.raises(MaskError):
        mask_env(None)  # type: ignore[arg-type]


def test_non_sensitive_key_unchanged():
    env = _env(APP_ENV="production", LOG_LEVEL="info")
    result = mask_env(env)
    assert result.masked["APP_ENV"] == "production"
    assert result.masked["LOG_LEVEL"] == "info"


def test_password_key_is_masked():
    env = _env(DB_PASSWORD="supersecret")
    result = mask_env(env)
    assert result.masked["DB_PASSWORD"] == MASK_PLACEHOLDER


def test_original_preserved_after_mask():
    env = _env(DB_PASSWORD="supersecret")
    result = mask_env(env)
    assert result.original["DB_PASSWORD"] == "supersecret"


def test_masked_keys_list_populated():
    env = _env(DB_PASSWORD="s", API_KEY="k", APP_ENV="prod")
    result = mask_env(env)
    assert "DB_PASSWORD" in result.masked_keys
    assert "API_KEY" in result.masked_keys
    assert "APP_ENV" not in result.masked_keys


def test_mask_count_matches_sensitive_keys():
    env = _env(SECRET_KEY="x", TOKEN="y", HOST="localhost")
    result = mask_env(env)
    assert result.mask_count == 2


def test_custom_placeholder():
    opts = MaskOptions(placeholder="<REDACTED>")
    env = _env(PASSWORD="abc")
    result = mask_env(env, options=opts)
    assert result.masked["PASSWORD"] == "<REDACTED>"


def test_empty_env_returns_empty_result():
    result = mask_env({})
    assert result.masked == {}
    assert result.mask_count == 0
