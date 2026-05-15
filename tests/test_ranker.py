"""Tests for envdiff.ranker."""
from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.ranker import RankError, RankResult, RankedKey, Severity, rank_result


def _make_result(
    left: dict | None = None,
    right: dict | None = None,
    mismatches: list | None = None,
) -> CompareResult:
    left = left or {}
    right = right or {}
    mismatches = mismatches or []
    missing_in_right = [k for k in left if k not in right]
    missing_in_left = [k for k in right if k not in left]
    return CompareResult(
        left=left,
        right=right,
        mismatches=mismatches,
        missing_in_right=missing_in_right,
        missing_in_left=missing_in_left,
    )


def test_rank_result_none_raises():
    with pytest.raises(RankError):
        rank_result(None)  # type: ignore[arg-type]


def test_no_diffs_all_ok():
    result = _make_result(left={"A": "1", "B": "2"}, right={"A": "1", "B": "2"})
    rank = rank_result(result)
    assert len(rank) == 2
    assert all(r.severity == Severity.OK for r in rank.ranked)


def test_missing_in_right_is_missing_severity():
    result = _make_result(left={"A": "1"}, right={})
    rank = rank_result(result)
    assert rank.ranked[0].severity == Severity.MISSING
    assert rank.ranked[0].right_value is None


def test_missing_in_left_is_missing_severity():
    result = _make_result(left={}, right={"B": "2"})
    rank = rank_result(result)
    assert rank.ranked[0].severity == Severity.MISSING
    assert rank.ranked[0].left_value is None


def test_mismatch_severity():
    diff = KeyDiff(key="X", left_value="a", right_value="b")
    result = _make_result(left={"X": "a"}, right={"X": "b"}, mismatches=[diff])
    rank = rank_result(result)
    mismatch_entries = [r for r in rank.ranked if r.severity == Severity.MISMATCH]
    assert len(mismatch_entries) == 1
    assert mismatch_entries[0].key == "X"


def test_by_severity_orders_missing_first():
    diff = KeyDiff(key="X", left_value="a", right_value="b")
    result = _make_result(
        left={"MISSING_KEY": "v", "X": "a"},
        right={"X": "b"},
        mismatches=[diff],
    )
    rank = rank_result(result)
    ordered = rank.by_severity()
    assert ordered[0].severity == Severity.MISSING
    assert ordered[1].severity == Severity.MISMATCH


def test_top_returns_correct_count():
    left = {f"K{i}": str(i) for i in range(5)}
    result = _make_result(left=left, right={})
    rank = rank_result(result)
    assert len(rank.top(3)) == 3


def test_top_zero_raises():
    result = _make_result(left={"A": "1"}, right={"A": "1"})
    rank = rank_result(result)
    with pytest.raises(RankError):
        rank.top(0)


def test_ranked_key_str():
    rk = RankedKey(key="MY_KEY", severity=Severity.MISSING)
    assert "MISSING" in str(rk)
    assert "MY_KEY" in str(rk)
