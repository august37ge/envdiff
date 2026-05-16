"""Tests for envdiff.inspector."""
from __future__ import annotations

import pathlib
import pytest

from envdiff.inspector import inspect_file, InspectError, KeyInspection


def _write(tmp_path: pathlib.Path, content: str) -> str:
    p = tmp_path / ".env"
    p.write_text(content)
    return str(p)


def test_missing_file_raises(tmp_path):
    with pytest.raises(InspectError, match="not found"):
        inspect_file(str(tmp_path / "nonexistent.env"))


def test_empty_file_returns_no_keys(tmp_path):
    path = _write(tmp_path, "\n# comment\n")
    result = inspect_file(path)
    assert result.total == 0
    assert result.keys == []


def test_basic_key_detected(tmp_path):
    path = _write(tmp_path, "FOO=bar\n")
    result = inspect_file(path)
    assert result.total == 1
    ki = result.keys[0]
    assert ki.key == "FOO"
    assert ki.value == "bar"
    assert not ki.is_empty
    assert not ki.is_numeric
    assert not ki.is_boolean
    assert not ki.is_url
    assert ki.char_count == 3


def test_empty_value_detected(tmp_path):
    path = _write(tmp_path, "EMPTY=\n")
    result = inspect_file(path)
    ki = result.find("EMPTY")
    assert ki is not None
    assert ki.is_empty


def test_numeric_value_detected(tmp_path):
    path = _write(tmp_path, "PORT=8080\n")
    result = inspect_file(path)
    ki = result.find("PORT")
    assert ki is not None
    assert ki.is_numeric
    assert not ki.is_empty


def test_boolean_value_detected(tmp_path):
    for val in ("true", "false", "yes", "no", "1", "0", "on", "off"):
        path = _write(tmp_path, f"FLAG={val}\n")
        ki = inspect_file(path).find("FLAG")
        assert ki is not None and ki.is_boolean, f"Expected boolean for value '{val}'"


def test_url_value_detected(tmp_path):
    path = _write(tmp_path, "DATABASE_URL=https://example.com/db\n")
    ki = inspect_file(path).find("DATABASE_URL")
    assert ki is not None
    assert ki.is_url


def test_whitespace_detected(tmp_path):
    path = _write(tmp_path, "KEY= value \n")
    ki = inspect_file(path).find("KEY")
    assert ki is not None
    assert ki.has_whitespace


def test_find_returns_none_for_missing_key(tmp_path):
    path = _write(tmp_path, "FOO=bar\n")
    result = inspect_file(path)
    assert result.find("MISSING") is None


def test_multiple_keys(tmp_path):
    path = _write(tmp_path, "A=1\nB=hello\nC=\n")
    result = inspect_file(path)
    assert result.total == 3
    assert {k.key for k in result.keys} == {"A", "B", "C"}
