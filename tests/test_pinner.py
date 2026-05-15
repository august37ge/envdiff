"""Tests for envdiff.pinner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.pinner import (
    PinEntry,
    PinError,
    diff_against_pin,
    load_pin,
    pin_file,
    save_pin,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_pin_file_returns_entry(tmp_path: Path) -> None:
    f = _write(tmp_path, ".env", "KEY=value\nFOO=bar\n")
    entry = pin_file(str(f))
    assert entry.values == {"KEY": "value", "FOO": "bar"}
    assert entry.pinned_at  # non-empty timestamp


def test_pin_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(PinError, match="not found"):
        pin_file(str(tmp_path / "ghost.env"))


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    f = _write(tmp_path, ".env", "A=1\nB=2\n")
    entry = pin_file(str(f))
    pin_path = tmp_path / "pin.json"
    save_pin(entry, str(pin_path))
    loaded = load_pin(str(pin_path))
    assert loaded.values == entry.values
    assert loaded.pinned_at == entry.pinned_at


def test_load_pin_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(PinError, match="not found"):
        load_pin(str(tmp_path / "no.json"))


def test_load_pin_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(PinError, match="Invalid pin"):
        load_pin(str(bad))


def test_diff_no_changes(tmp_path: Path) -> None:
    f = _write(tmp_path, ".env", "X=1\n")
    entry = pin_file(str(f))
    result = diff_against_pin(str(f), entry)
    assert result == {"added": {}, "removed": {}, "changed": {}}


def test_diff_detects_added_key(tmp_path: Path) -> None:
    f = _write(tmp_path, ".env", "X=1\n")
    entry = pin_file(str(f))
    f.write_text("X=1\nNEW=hello\n", encoding="utf-8")
    result = diff_against_pin(str(f), entry)
    assert "NEW" in result["added"]
    assert result["removed"] == {}
    assert result["changed"] == {}


def test_diff_detects_removed_key(tmp_path: Path) -> None:
    f = _write(tmp_path, ".env", "X=1\nOLD=bye\n")
    entry = pin_file(str(f))
    f.write_text("X=1\n", encoding="utf-8")
    result = diff_against_pin(str(f), entry)
    assert "OLD" in result["removed"]


def test_diff_detects_changed_value(tmp_path: Path) -> None:
    f = _write(tmp_path, ".env", "X=old\n")
    entry = pin_file(str(f))
    f.write_text("X=new\n", encoding="utf-8")
    result = diff_against_pin(str(f), entry)
    assert result["changed"]["X"] == {"pinned": "old", "current": "new"}
