"""Tests for envdiff.streaker and envdiff.streaker_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.streaker import (
    StreakRecord,
    StreakerError,
    load_streak,
    record_run,
    save_streak,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# StreakRecord unit tests
# ---------------------------------------------------------------------------

def test_record_run_increments_streak_on_clean():
    rec = StreakRecord(left="a.env", right="b.env")
    record_run(rec, is_clean=True, ts=1000.0)
    assert rec.current_streak == 1
    assert rec.best_streak == 1
    assert rec.last_run_clean is True


def test_record_run_resets_streak_on_dirty():
    rec = StreakRecord(left="a.env", right="b.env", current_streak=5, best_streak=5)
    record_run(rec, is_clean=False, ts=2000.0)
    assert rec.current_streak == 0
    assert rec.best_streak == 5  # best preserved
    assert rec.last_run_clean is False


def test_best_streak_updated_when_exceeded():
    rec = StreakRecord(left="a.env", right="b.env", current_streak=3, best_streak=3)
    record_run(rec, is_clean=True)
    assert rec.best_streak == 4


def test_best_streak_not_lowered_after_reset():
    rec = StreakRecord(left="a.env", right="b.env", current_streak=10, best_streak=10)
    record_run(rec, is_clean=False)
    record_run(rec, is_clean=True)
    assert rec.best_streak == 10
    assert rec.current_streak == 1


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    rec = StreakRecord(left="x.env", right="y.env", current_streak=7, best_streak=7)
    p = tmp_path / "streak.json"
    save_streak(rec, p)
    loaded = load_streak(p)
    assert loaded.current_streak == 7
    assert loaded.best_streak == 7
    assert loaded.left == "x.env"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(StreakerError):
        load_streak(tmp_path / "nonexistent.json")


def test_load_corrupt_json_raises(tmp_path):
    p = _write(tmp_path / "bad.json", "{not valid json")
    with pytest.raises(StreakerError):
        load_streak(p)


def test_save_creates_valid_json(tmp_path):
    rec = StreakRecord(left="a.env", right="b.env")
    p = tmp_path / "streak.json"
    save_streak(rec, p)
    data = json.loads(p.read_text())
    assert data["left"] == "a.env"
    assert "current_streak" in data


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

def test_streaker_cli_record_clean(tmp_path):
    left = _write(tmp_path / "left.env", "KEY=val\n")
    right = _write(tmp_path / "right.env", "KEY=val\n")
    streak_file = tmp_path / "streak.json"

    from envdiff.streaker_cli import _cmd_record
    import argparse

    args = argparse.Namespace(left=str(left), right=str(right), streak_file=str(streak_file))
    exit_code = _cmd_record(args)
    assert exit_code == 0
    rec = load_streak(streak_file)
    assert rec.current_streak == 1


def test_streaker_cli_record_dirty_exits_2(tmp_path):
    left = _write(tmp_path / "left.env", "KEY=val\n")
    right = _write(tmp_path / "right.env", "KEY=other\n")
    streak_file = tmp_path / "streak.json"

    from envdiff.streaker_cli import _cmd_record
    import argparse

    args = argparse.Namespace(left=str(left), right=str(right), streak_file=str(streak_file))
    exit_code = _cmd_record(args)
    assert exit_code == 2
    rec = load_streak(streak_file)
    assert rec.current_streak == 0


def test_streaker_cli_show_missing_file_returns_1(tmp_path):
    import argparse
    from envdiff.streaker_cli import _cmd_show

    args = argparse.Namespace(streak_file=str(tmp_path / "nope.json"))
    assert _cmd_show(args) == 1
