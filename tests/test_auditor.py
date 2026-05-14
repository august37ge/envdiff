"""Tests for envdiff.auditor."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.auditor import AuditError, audit_file


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_no_issues_for_clean_file(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "APP_ENV=production\nDEBUG=false\n")
    result = audit_file(p)
    assert not result.has_issues


def test_sensitive_key_with_plaintext_value_warns(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "API_KEY=supersecretvalue123\n")
    result = audit_file(p)
    assert result.has_issues
    assert any("plaintext" in i.message for i in result.warnings)


def test_sensitive_key_empty_value_warns(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "DB_PASSWORD=\n")
    result = audit_file(p)
    assert result.has_issues
    warn = result.warnings[0]
    assert warn.key == "DB_PASSWORD"
    assert "empty" in warn.message


def test_non_sensitive_empty_value_is_info(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "OPTIONAL_FEATURE=\n")
    result = audit_file(p)
    assert result.has_issues
    assert result.infos
    assert not result.warnings


def test_audit_error_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(AuditError, match="File not found"):
        audit_file(tmp_path / "nonexistent.env")


def test_multiple_issues_detected(tmp_path: Path) -> None:
    content = "SECRET_TOKEN=abc123xyz\nDB_PASS=\nPLAIN_KEY=\n"
    p = _write(tmp_path, ".env", content)
    result = audit_file(p)
    assert len(result.issues) == 3
    assert len(result.warnings) == 2
    assert len(result.infos) == 1


def test_issue_str_representation(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "API_KEY=mysecretvalue99\n")
    result = audit_file(p)
    assert result.has_issues
    s = str(result.issues[0])
    assert "[WARN]" in s
    assert "API_KEY" in s


def test_comments_and_blank_lines_not_flagged(tmp_path: Path) -> None:
    content = "# This is a comment\n\nAPP_NAME=envdiff\n"
    p = _write(tmp_path, ".env", content)
    result = audit_file(p)
    assert not result.has_issues
