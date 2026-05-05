"""Tests for envdiff.parser module."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError


def write_env(tmp_path: Path, content: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(content, encoding="utf-8")
    return env_file


def test_basic_key_value(tmp_path):
    f = write_env(tmp_path, "APP_NAME=myapp\nDEBUG=true\n")
    result = parse_env_file(f)
    assert result == {"APP_NAME": "myapp", "DEBUG": "true"}


def test_quoted_values(tmp_path):
    f = write_env(tmp_path, 'DB_URL="postgres://localhost/db"\nSECRET=\'abc123\'\n')
    result = parse_env_file(f)
    assert result["DB_URL"] == "postgres://localhost/db"
    assert result["SECRET"] == "abc123"


def test_comments_and_blank_lines_ignored(tmp_path):
    content = "# This is a comment\n\nAPP_ENV=production\n"
    f = write_env(tmp_path, content)
    result = parse_env_file(f)
    assert result == {"APP_ENV": "production"}


def test_empty_value(tmp_path):
    f = write_env(tmp_path, "EMPTY_KEY=\n")
    result = parse_env_file(f)
    assert result["EMPTY_KEY"] is None


def test_bare_key_no_equals(tmp_path):
    f = write_env(tmp_path, "BARE_KEY\n")
    result = parse_env_file(f)
    assert result["BARE_KEY"] is None


def test_file_not_found():
    with pytest.raises(EnvParseError, match="File not found"):
        parse_env_file("/nonexistent/path/.env")


def test_invalid_key_starts_with_digit(tmp_path):
    f = write_env(tmp_path, "1INVALID=value\n")
    with pytest.raises(EnvParseError, match="Invalid key"):
        parse_env_file(f)


def test_invalid_key_with_special_chars(tmp_path):
    f = write_env(tmp_path, "MY-KEY=value\n")
    with pytest.raises(EnvParseError, match="Invalid key"):
        parse_env_file(f)


def test_multiple_equals_in_value(tmp_path):
    f = write_env(tmp_path, "TOKEN=abc=def=ghi\n")
    result = parse_env_file(f)
    assert result["TOKEN"] == "abc=def=ghi"


def test_empty_file(tmp_path):
    f = write_env(tmp_path, "")
    result = parse_env_file(f)
    assert result == {}


def test_underscore_in_key(tmp_path):
    f = write_env(tmp_path, "MY_LONG_KEY_NAME=123\n")
    result = parse_env_file(f)
    assert result["MY_LONG_KEY_NAME"] == "123"
