"""Tests for envdiff.differ_stats."""
from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.differ_stats import DiffStats, StatsError, compute_stats


def _make_result(
    missing_left=(),
    missing_right=(),
    mismatches=(),
) -> CompareResult:
    diffs = [KeyDiff(key=k, left_value="a", right_value="b") for k in mismatches]
    return CompareResult(
        missing_in_left=list(missing_left),
        missing_in_right=list(missing_right),
        mismatches=diffs,
    )


def test_empty_list_raises():
    with pytest.raises(StatsError):
        compute_stats([])


def test_all_none_raises():
    with pytest.raises(StatsError):
        compute_stats([None, None])


def test_no_diffs_perfect_health():
    result = _make_result()
    stats = compute_stats([result])
    assert stats.total_diffs == 0
    assert stats.health_pct == 100.0
    assert stats.file_count == 1


def test_missing_right_counted():
    result = _make_result(missing_right=["KEY_A", "KEY_B"])
    stats = compute_stats([result])
    assert stats.total_missing_right == 2
    assert stats.total_missing_left == 0
    assert stats.total_mismatches == 0
    assert stats.total_diffs == 2


def test_missing_left_counted():
    result = _make_result(missing_left=["X"])
    stats = compute_stats([result])
    assert stats.total_missing_left == 1
    assert stats.total_diffs == 1


def test_mismatch_counted():
    result = _make_result(mismatches=["DB_URL"])
    stats = compute_stats([result])
    assert stats.total_mismatches == 1
    assert stats.total_diffs == 1


def test_multiple_results_aggregated():
    r1 = _make_result(missing_right=["A"])
    r2 = _make_result(missing_left=["B"], mismatches=["C"])
    stats = compute_stats([r1, r2])
    assert stats.file_count == 2
    assert stats.total_missing_right == 1
    assert stats.total_missing_left == 1
    assert stats.total_mismatches == 1
    assert stats.total_diffs == 3


def test_none_entries_skipped():
    result = _make_result(missing_right=["KEY"])
    stats = compute_stats([None, result, None])
    assert stats.file_count == 1
    assert stats.total_missing_right == 1


def test_str_representation_contains_health():
    result = _make_result()
    stats = compute_stats([result])
    s = str(stats)
    assert "Health" in s
    assert "100.0%" in s


def test_health_pct_partial():
    # 2 diffs out of 4 total keys => 50%
    result = _make_result(missing_right=["A", "B"])
    # total_keys = 2 (missing_right), ok = 0
    stats = compute_stats([result])
    assert stats.health_pct == 0.0  # all keys are diffs, none are ok
