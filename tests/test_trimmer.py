"""Tests for envdiff.trimmer."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.trimmer import TrimError, TrimEntry, TrimResult, trim_file, write_trimmed


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_trim_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(TrimError, match="not found"):
        trim_file(tmp_path / "ghost.env")


def test_no_whitespace_no_changes(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "KEY=value\nFOO=bar\n")
    result = trim_file(p)
    assert not result.has_changes
    assert result.changed_entries == []


def test_leading_whitespace_detected(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "KEY=  hello\n")
    result = trim_file(p)
    assert result.has_changes
    assert result.changed_entries[0].key == "KEY"
    assert result.changed_entries[0].trimmed == "hello"


def test_trailing_whitespace_detected(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "KEY=world   \n")
    result = trim_file(p)
    assert result.has_changes
    assert result.changed_entries[0].trimmed == "world"


def test_both_sides_trimmed(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "KEY=  padded  \n")
    result = trim_file(p)
    entry = result.changed_entries[0]
    assert entry.original == "  padded  "
    assert entry.trimmed == "padded"


def test_as_dict_returns_trimmed_values(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "A= 1 \nB=2\n")
    result = trim_file(p)
    d = result.as_dict()
    assert d["A"] == "1"
    assert d["B"] == "2"


def test_write_trimmed_creates_file(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "KEY=  hello  \nFOO=bar\n")
    result = trim_file(p)
    out = tmp_path / "trimmed.env"
    write_trimmed(result, out)
    assert out.exists()
    lines = out.read_text().splitlines()
    assert "KEY=hello" in lines
    assert "FOO=bar" in lines


def test_trim_entry_str(tmp_path: Path) -> None:
    entry = TrimEntry(key="X", original=" v ", trimmed="v")
    assert "X" in str(entry)
    assert "->" in str(entry)


def test_source_recorded(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "K=v\n")
    result = trim_file(p)
    assert result.source == str(p)
