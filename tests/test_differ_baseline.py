"""Tests for envdiff.differ_baseline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.differ_baseline import BaselineError, diff_against_baseline


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _write_snapshot(path: Path, left: dict[str, str]) -> Path:
    """Write a minimal snapshot JSON that diff_against_baseline can read."""
    data = {
        "left": left,
        "right": {},
        "diffs": [],
    }
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# happy-path tests
# ---------------------------------------------------------------------------

def test_in_sync_returns_no_diffs(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {"A": "1", "B": "2"})
    env = _write(tmp_path / ".env", "A=1\nB=2\n")
    result = diff_against_baseline(env, snap)
    assert not result.has_diffs


def test_added_key_detected(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {"A": "1"})
    env = _write(tmp_path / ".env", "A=1\nB=2\n")
    result = diff_against_baseline(env, snap)
    # B is in live but not in baseline → missing_in_left of the compare
    assert any(d.key == "B" for d in result.compare.missing_in_left)


def test_removed_key_detected(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {"A": "1", "B": "2"})
    env = _write(tmp_path / ".env", "A=1\n")
    result = diff_against_baseline(env, snap)
    assert any(d.key == "B" for d in result.compare.missing_in_right)


def test_changed_value_detected(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {"A": "old"})
    env = _write(tmp_path / ".env", "A=new\n")
    result = diff_against_baseline(env, snap)
    assert any(d.key == "A" for d in result.compare.mismatched)


def test_keys_only_ignores_value_change(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {"A": "old"})
    env = _write(tmp_path / ".env", "A=new\n")
    result = diff_against_baseline(env, snap, keys_only=True)
    assert not result.has_diffs


def test_summary_in_sync(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {"X": "1"})
    env = _write(tmp_path / ".env", "X=1\n")
    result = diff_against_baseline(env, snap)
    assert "in sync" in result.summary()


def test_summary_drifted(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {"X": "1", "Y": "2"})
    env = _write(tmp_path / ".env", "X=changed\n")
    result = diff_against_baseline(env, snap)
    assert "drifted" in result.summary()


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_missing_env_raises(tmp_path):
    snap = _write_snapshot(tmp_path / "base.json", {})
    with pytest.raises(BaselineError, match="Env file not found"):
        diff_against_baseline(tmp_path / "missing.env", snap)


def test_missing_baseline_raises(tmp_path):
    env = _write(tmp_path / ".env", "A=1\n")
    with pytest.raises(BaselineError, match="Baseline snapshot not found"):
        diff_against_baseline(env, tmp_path / "no_snap.json")


def test_invalid_baseline_json_raises(tmp_path):
    snap = _write(tmp_path / "bad.json", "not json{{{")
    env = _write(tmp_path / ".env", "A=1\n")
    with pytest.raises(BaselineError, match="Failed to load baseline"):
        diff_against_baseline(env, snap)
