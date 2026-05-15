"""Tests for envdiff.sorter."""
from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.sorter import SortError, SortKey, SortOptions, sort_diffs


def _make_result(*diffs: KeyDiff) -> CompareResult:
    return CompareResult(diffs=list(diffs))


def _kd(key: str, left=None, right=None) -> KeyDiff:
    return KeyDiff(key=key, left_value=left, right_value=right)


# ---------------------------------------------------------------------------
# sort_diffs – error handling
# ---------------------------------------------------------------------------

def test_sort_result_none_raises():
    with pytest.raises(SortError):
        sort_diffs(None)


# ---------------------------------------------------------------------------
# sort by name (default)
# ---------------------------------------------------------------------------

def test_default_sort_is_alphabetical():
    result = _make_result(_kd("ZEBRA"), _kd("ALPHA"), _kd("MIDDLE"))
    sorted_diffs = sort_diffs(result)
    assert [d.key for d in sorted_diffs] == ["ALPHA", "MIDDLE", "ZEBRA"]


def test_sort_by_name_reverse():
    result = _make_result(_kd("ALPHA"), _kd("ZEBRA"), _kd("MIDDLE"))
    opts = SortOptions(key=SortKey.NAME, reverse=True)
    sorted_diffs = sort_diffs(result, opts)
    assert [d.key for d in sorted_diffs] == ["ZEBRA", "MIDDLE", "ALPHA"]


# ---------------------------------------------------------------------------
# sort by severity
# ---------------------------------------------------------------------------

def test_sort_by_severity_missing_left_first():
    result = _make_result(
        _kd("C", left="v", right="v"),       # ok
        _kd("B", left="v1", right="v2"),     # mismatch
        _kd("A", left=None, right="v"),      # missing_left
    )
    opts = SortOptions(key=SortKey.SEVERITY)
    sorted_diffs = sort_diffs(result, opts)
    assert sorted_diffs[0].key == "A"        # missing_left
    assert sorted_diffs[1].key == "B"        # mismatch
    assert sorted_diffs[2].key == "C"        # ok


def test_sort_by_severity_missing_right_before_mismatch():
    result = _make_result(
        _kd("M", left="x", right="y"),       # mismatch
        _kd("R", left="x", right=None),      # missing_right
    )
    opts = SortOptions(key=SortKey.SEVERITY)
    sorted_diffs = sort_diffs(result, opts)
    assert sorted_diffs[0].key == "R"
    assert sorted_diffs[1].key == "M"


def test_sort_by_severity_same_rank_sorted_by_name():
    result = _make_result(
        _kd("ZEBRA", left=None, right="v"),
        _kd("ALPHA", left=None, right="v"),
    )
    opts = SortOptions(key=SortKey.SEVERITY)
    sorted_diffs = sort_diffs(result, opts)
    assert [d.key for d in sorted_diffs] == ["ALPHA", "ZEBRA"]


# ---------------------------------------------------------------------------
# sort by status (alias for severity ordering)
# ---------------------------------------------------------------------------

def test_sort_by_status_equivalent_to_severity():
    result = _make_result(
        _kd("B", left="a", right="b"),
        _kd("A", left=None, right="v"),
    )
    sev = sort_diffs(result, SortOptions(key=SortKey.SEVERITY))
    sta = sort_diffs(result, SortOptions(key=SortKey.STATUS))
    assert [d.key for d in sev] == [d.key for d in sta]


# ---------------------------------------------------------------------------
# empty result
# ---------------------------------------------------------------------------

def test_empty_result_returns_empty_list():
    result = _make_result()
    assert sort_diffs(result) == []
