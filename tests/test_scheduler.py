"""Tests for envdiff.scheduler."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.scheduler import (
    ScheduleEntry,
    ScheduleLog,
    SchedulerError,
    load_log,
    record_run,
    save_log,
)


def _make_result(*, ml: list[str] = (), mr: list[str] = (), mm: list[tuple] = ()) -> CompareResult:
    diffs = [
        KeyDiff(key=k, left_value=None, right_value="x") for k in ml
    ] + [
        KeyDiff(key=k, left_value="x", right_value=None) for k in mr
    ] + [
        KeyDiff(key=k, left_value=lv, right_value=rv) for k, lv, rv in mm
    ]
    return CompareResult(diffs=diffs)


def test_record_run_no_diffs():
    result = _make_result()
    entry = record_run("a.env", "b.env", result, clock=lambda: 1000.0)
    assert entry.has_diffs is False
    assert entry.missing_in_left == 0
    assert entry.missing_in_right == 0
    assert entry.mismatches == 0
    assert entry.timestamp == 1000.0


def test_record_run_with_diffs():
    result = _make_result(ml=["FOO"], mr=["BAR"], mm=[("BAZ", "1", "2")])
    entry = record_run("a.env", "b.env", result)
    assert entry.has_diffs is True
    assert entry.missing_in_left == 1
    assert entry.missing_in_right == 1
    assert entry.mismatches == 1


def test_entry_roundtrip():
    entry = ScheduleEntry(
        timestamp=999.9,
        left="l.env",
        right="r.env",
        has_diffs=True,
        missing_in_left=2,
        missing_in_right=1,
        mismatches=3,
    )
    assert ScheduleEntry.from_dict(entry.to_dict()) == entry


def test_save_creates_file(tmp_path: Path):
    log_path = tmp_path / "sched.json"
    result = _make_result()
    entry = record_run("a.env", "b.env", result, clock=time.time)
    log = ScheduleLog(entries=[entry])
    save_log(log, log_path)
    assert log_path.exists()


def test_save_appends_to_existing(tmp_path: Path):
    log_path = tmp_path / "sched.json"
    result = _make_result()
    e1 = record_run("a.env", "b.env", result, clock=lambda: 1.0)
    e2 = record_run("a.env", "b.env", result, clock=lambda: 2.0)
    save_log(ScheduleLog(entries=[e1]), log_path)
    save_log(ScheduleLog(entries=[e2]), log_path)
    loaded = load_log(log_path)
    assert len(loaded.entries) == 2
    assert loaded.entries[0].timestamp == 1.0
    assert loaded.entries[1].timestamp == 2.0


def test_load_missing_raises(tmp_path: Path):
    with pytest.raises(SchedulerError, match="not found"):
        load_log(tmp_path / "missing.json")


def test_load_corrupt_raises(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    with pytest.raises(SchedulerError):
        load_log(bad)


def test_log_to_dict_structure(tmp_path: Path):
    result = _make_result(mr=["KEY"])
    entry = record_run("a.env", "b.env", result, clock=lambda: 42.0)
    log = ScheduleLog(entries=[entry])
    log_path = tmp_path / "s.json"
    save_log(log, log_path)
    data = json.loads(log_path.read_text())
    assert "entries" in data
    assert data["entries"][0]["has_diffs"] is True
    assert data["entries"][0]["timestamp"] == 42.0
