"""Tests for envdiff.filterer."""

from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.filterer import FilterError, FilterOptions, filter_result


def _make_result(*diffs: KeyDiff) -> CompareResult:
    return CompareResult(left_path="a.env", right_path="b.env", diffs=list(diffs))


DIFF_MISSING_RIGHT = KeyDiff(key="DB_HOST", left_value="localhost", right_value=None)
DIFF_MISSING_LEFT = KeyDiff(key="API_KEY", left_value=None, right_value="secret")
DIFF_MISMATCH = KeyDiff(key="PORT", left_value="5432", right_value="3306")
DIFF_OTHER = KeyDiff(key="DEBUG", left_value="true", right_value="false")


def test_no_options_returns_all_diffs():
    result = _make_result(DIFF_MISSING_RIGHT, DIFF_MISMATCH)
    out = filter_result(result, FilterOptions())
    assert len(out.diffs) == 2


def test_glob_pattern_includes_matching_keys():
    result = _make_result(DIFF_MISSING_RIGHT, DIFF_MISMATCH, DIFF_OTHER)
    out = filter_result(result, FilterOptions(pattern="DB_*"))
    assert [d.key for d in out.diffs] == ["DB_HOST"]


def test_regex_pattern_matches():
    result = _make_result(DIFF_MISSING_RIGHT, DIFF_MISMATCH, DIFF_OTHER)
    out = filter_result(result, FilterOptions(pattern=r"^(PORT|DEBUG)$", use_regex=True))
    assert {d.key for d in out.diffs} == {"PORT", "DEBUG"}


def test_exclude_pattern_removes_keys():
    result = _make_result(DIFF_MISSING_RIGHT, DIFF_MISMATCH, DIFF_OTHER)
    out = filter_result(result, FilterOptions(exclude_pattern="PORT"))
    assert "PORT" not in {d.key for d in out.diffs}
    assert len(out.diffs) == 2


def test_missing_only_excludes_mismatches():
    result = _make_result(DIFF_MISSING_RIGHT, DIFF_MISSING_LEFT, DIFF_MISMATCH)
    out = filter_result(result, FilterOptions(missing_only=True))
    assert all(d.left_value is None or d.right_value is None for d in out.diffs)
    assert len(out.diffs) == 2


def test_mismatch_only_excludes_missing():
    result = _make_result(DIFF_MISSING_RIGHT, DIFF_MISMATCH, DIFF_OTHER)
    out = filter_result(result, FilterOptions(mismatch_only=True))
    assert all(d.left_value is not None and d.right_value is not None for d in out.diffs)
    assert len(out.diffs) == 2


def test_missing_and_mismatch_only_raises():
    result = _make_result(DIFF_MISMATCH)
    with pytest.raises(FilterError, match="mutually exclusive"):
        filter_result(result, FilterOptions(missing_only=True, mismatch_only=True))


def test_invalid_regex_raises():
    result = _make_result(DIFF_MISMATCH)
    with pytest.raises(FilterError, match="Invalid regex"):
        filter_result(result, FilterOptions(pattern="[invalid", use_regex=True))


def test_metadata_preserved():
    result = _make_result(DIFF_MISMATCH)
    out = filter_result(result, FilterOptions())
    assert out.left_path == "a.env"
    assert out.right_path == "b.env"
