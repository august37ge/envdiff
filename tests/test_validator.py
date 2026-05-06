"""Tests for envdiff.validator module."""

import pytest

from envdiff.validator import ValidationIssue, ValidationResult, validate_env_file


@pytest.fixture()
def write_env(tmp_path):
    def _write(filename: str, content: str):
        p = tmp_path / filename
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


def test_valid_file_returns_no_issues(write_env):
    path = write_env("good.env", "KEY=value\nFOO=bar\n")
    result = validate_env_file(path)
    assert result.is_valid
    assert result.issues == []


def test_comments_and_blanks_ignored(write_env):
    path = write_env("comments.env", "# comment\n\nKEY=value\n")
    result = validate_env_file(path)
    assert result.is_valid


def test_missing_equals_reported(write_env):
    path = write_env("bad.env", "MISSING_EQUALS\nGOOD=ok\n")
    result = validate_env_file(path)
    assert not result.is_valid
    assert len(result.issues) == 1
    assert "Missing '='" in result.issues[0].message
    assert result.issues[0].line_number == 1


def test_empty_key_reported(write_env):
    path = write_env("emptykey.env", "=value\n")
    result = validate_env_file(path)
    assert not result.is_valid
    assert any("Empty key" in i.message for i in result.issues)


def test_key_with_whitespace_reported(write_env):
    path = write_env("spaces.env", "MY KEY=value\n")
    result = validate_env_file(path)
    assert not result.is_valid
    assert any("whitespace" in i.message for i in result.issues)


def test_unclosed_double_quote_reported(write_env):
    path = write_env("quote.env", 'KEY="unclosed\n')
    result = validate_env_file(path)
    assert not result.is_valid
    assert any("Unclosed quote" in i.message for i in result.issues)


def test_unclosed_single_quote_reported(write_env):
    path = write_env("squote.env", "KEY='unclosed\n")
    result = validate_env_file(path)
    assert not result.is_valid
    assert any("Unclosed quote" in i.message for i in result.issues)


def test_properly_quoted_value_ok(write_env):
    path = write_env("quoted.env", 'KEY="hello world"\n')
    result = validate_env_file(path)
    assert result.is_valid


def test_missing_file_reports_issue():
    result = validate_env_file("/nonexistent/path/.env")
    assert not result.is_valid
    assert any("Cannot read file" in i.message for i in result.issues)


def test_str_valid(write_env):
    path = write_env("ok.env", "A=1\n")
    result = validate_env_file(path)
    assert "OK" in str(result)


def test_str_invalid(write_env):
    path = write_env("bad2.env", "NO_EQUALS\n")
    result = validate_env_file(path)
    output = str(result)
    assert "1 issue" in output
    assert "Line 1" in output
