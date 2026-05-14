"""Tests for envdiff.linter."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.linter import lint_file, LintError, LintResult, LintIssue


def _write(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_clean_file_returns_no_issues(tmp_path):
    path = _write(tmp_path, ".env", "APP_NAME=myapp\nDEBUG=false\n")
    result = lint_file(path)
    assert isinstance(result, LintResult)
    assert result.is_clean
    assert result.issues == []


def test_lowercase_key_triggers_e001(tmp_path):
    path = _write(tmp_path, ".env", "app_name=myapp\n")
    result = lint_file(path)
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_mixed_case_key_triggers_e001(tmp_path):
    path = _write(tmp_path, ".env", "AppName=test\n")
    result = lint_file(path)
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_double_underscore_triggers_e002(tmp_path):
    path = _write(tmp_path, ".env", "APP__NAME=foo\n")
    result = lint_file(path)
    codes = [i.code for i in result.issues]
    assert "E002" in codes


def test_unquoted_value_with_spaces_triggers_w001(tmp_path):
    path = _write(tmp_path, ".env", "APP_TITLE=hello world\n")
    result = lint_file(path)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_quoted_value_with_spaces_is_ok(tmp_path):
    path = _write(tmp_path, ".env", 'APP_TITLE="hello world"\n')
    result = lint_file(path)
    codes = [i.code for i in result.issues]
    assert "W001" not in codes


def test_comments_and_blanks_ignored(tmp_path):
    content = "# comment\n\nAPP_KEY=value\n"
    path = _write(tmp_path, ".env", content)
    result = lint_file(path)
    assert result.is_clean


def test_missing_file_raises_lint_error(tmp_path):
    with pytest.raises(LintError, match="File not found"):
        lint_file(str(tmp_path / "nonexistent.env"))


def test_lint_issue_str(tmp_path):
    path = _write(tmp_path, ".env", "bad_key=value\n")
    result = lint_file(path)
    issue_str = str(result.issues[0])
    assert "E001" in issue_str
    assert "bad_key" in issue_str


def test_lint_result_str_with_issues(tmp_path):
    path = _write(tmp_path, ".env", "bad_key=hello world\n")
    result = lint_file(path)
    text = str(result)
    assert path in text
    assert "E001" in text or "W001" in text


def test_lint_result_str_clean(tmp_path):
    path = _write(tmp_path, ".env", "GOOD_KEY=value\n")
    result = lint_file(path)
    assert "no lint issues" in str(result)
