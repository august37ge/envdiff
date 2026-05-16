"""Tests for envdiff.deduplicator."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.deduplicator import (
    DeduplicatorError,
    DeduplicateResult,
    DuplicateEntry,
    find_duplicates,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_no_duplicates_returns_clean_result(tmp_path):
    p = _write(tmp_path, ".env", "FOO=bar\nBAZ=qux\n")
    result = find_duplicates(p)
    assert not result.has_duplicates
    assert result.duplicates == []


def test_single_duplicate_detected(tmp_path):
    p = _write(tmp_path, ".env", "FOO=first\nBAR=ok\nFOO=second\n")
    result = find_duplicates(p)
    assert result.has_duplicates
    assert len(result.duplicates) == 1
    entry = result.duplicates[0]
    assert entry.key == "FOO"
    assert entry.occurrences == [1, 3]


def test_multiple_duplicates_detected(tmp_path):
    content = "A=1\nB=2\nA=3\nB=4\nB=5\n"
    p = _write(tmp_path, ".env", content)
    result = find_duplicates(p)
    assert len(result.duplicates) == 2
    keys = [d.key for d in result.duplicates]
    assert "A" in keys
    assert "B" in keys


def test_comments_and_blanks_not_counted(tmp_path):
    content = "# FOO=comment\n\nFOO=real\n"
    p = _write(tmp_path, ".env", content)
    result = find_duplicates(p)
    assert not result.has_duplicates


def test_three_occurrences_all_recorded(tmp_path):
    p = _write(tmp_path, ".env", "KEY=a\nKEY=b\nKEY=c\n")
    result = find_duplicates(p)
    assert result.duplicates[0].occurrences == [1, 2, 3]


def test_missing_file_raises(tmp_path):
    with pytest.raises(DeduplicatorError, match="not found"):
        find_duplicates(tmp_path / "ghost.env")


def test_str_no_duplicates(tmp_path):
    p = _write(tmp_path, ".env", "X=1\n")
    result = find_duplicates(p)
    assert "no duplicate" in str(result)


def test_str_with_duplicates(tmp_path):
    p = _write(tmp_path, ".env", "X=1\nX=2\n")
    result = find_duplicates(p)
    text = str(result)
    assert "1 duplicate" in text
    assert "X" in text


def test_duplicate_entry_str():
    entry = DuplicateEntry(key="MY_KEY", occurrences=[2, 7, 11])
    assert "MY_KEY" in str(entry)
    assert "2" in str(entry)
    assert "11" in str(entry)


def test_result_path_preserved(tmp_path):
    p = _write(tmp_path, "prod.env", "A=1\n")
    result = find_duplicates(p)
    assert result.path == p
