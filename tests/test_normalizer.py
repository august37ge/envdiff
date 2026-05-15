"""Tests for envdiff.normalizer."""

from __future__ import annotations

import pytest

from envdiff.normalizer import (
    NormalizeError,
    NormalizeOptions,
    normalize_env,
    normalize_key,
    normalize_value,
)


# ---------------------------------------------------------------------------
# normalize_value
# ---------------------------------------------------------------------------

def test_double_quoted_value_stripped():
    assert normalize_value('"hello world"') == "hello world"


def test_single_quoted_value_stripped():
    assert normalize_value("'hello'") == "hello"


def test_unquoted_value_unchanged():
    assert normalize_value("plain") == "plain"


def test_mismatched_quotes_not_stripped():
    assert normalize_value('"mixed\'') == '"mixed\''


def test_escape_newline_expanded():
    assert normalize_value('line1\\nline2') == "line1\nline2"


def test_escape_tab_expanded():
    assert normalize_value('col1\\tcol2') == "col1\tcol2"


def test_escape_backslash_expanded():
    assert normalize_value('back\\\\slash') == "back\\slash"


def test_no_strip_quotes_option():
    opts = NormalizeOptions(strip_quotes=False)
    assert normalize_value('"quoted"', opts) == '"quoted"'


def test_no_expand_escapes_option():
    opts = NormalizeOptions(expand_escapes=False)
    assert normalize_value('a\\nb', opts) == 'a\\nb'


# ---------------------------------------------------------------------------
# normalize_key
# ---------------------------------------------------------------------------

def test_key_unchanged_by_default():
    assert normalize_key("MY_KEY") == "MY_KEY"


def test_key_lowercased_when_option_set():
    opts = NormalizeOptions(lowercase_keys=True)
    assert normalize_key("MY_KEY", opts) == "my_key"


# ---------------------------------------------------------------------------
# normalize_env
# ---------------------------------------------------------------------------

def test_normalize_env_strips_quotes_and_expands():
    env = {"DB_HOST": '"localhost"', "DB_PORT": "5432"}
    result = normalize_env(env)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_normalize_env_lowercase_keys():
    opts = NormalizeOptions(lowercase_keys=True)
    env = {"APP_ENV": "production"}
    result = normalize_env(env, opts)
    assert "app_env" in result
    assert result["app_env"] == "production"


def test_normalize_env_duplicate_key_after_lowercase_raises():
    opts = NormalizeOptions(lowercase_keys=True)
    env = {"KEY": "a", "key": "b"}
    with pytest.raises(NormalizeError, match="Duplicate key"):
        normalize_env(env, opts)


def test_normalize_env_empty_dict():
    assert normalize_env({}) == {}


def test_normalize_env_preserves_empty_value():
    result = normalize_env({"EMPTY": ""})
    assert result["EMPTY"] == ""
