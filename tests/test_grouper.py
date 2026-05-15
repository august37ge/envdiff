"""Tests for envdiff.grouper."""
from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.grouper import GroupError, KeyGroup, group_by_prefix


def _make_result(
    missing_right=(),
    missing_left=(),
    mismatches=(),
) -> CompareResult:
    mismatch_map = {
        k: KeyDiff(key=k, left_value=lv, right_value=rv)
        for k, lv, rv in mismatches
    }
    return CompareResult(
        missing_in_right=list(missing_right),
        missing_in_left=list(missing_left),
        mismatches=mismatch_map,
    )


def test_group_by_inferred_prefix_single_group():
    result = _make_result(missing_right=["DB_HOST", "DB_PORT", "DB_NAME"])
    gr = group_by_prefix(result)
    assert "DB" in gr.groups
    assert len(gr.groups["DB"]) == 3
    assert gr.ungrouped == []


def test_group_by_explicit_prefixes():
    result = _make_result(
        missing_right=["AWS_KEY", "AWS_SECRET"],
        missing_left=["APP_DEBUG"],
    )
    gr = group_by_prefix(result, prefixes=["AWS", "APP"])
    assert len(gr.groups["AWS"]) == 2
    assert len(gr.groups["APP"]) == 1
    assert gr.ungrouped == []


def test_ungrouped_keys_when_no_prefix_match():
    result = _make_result(missing_right=["SECRET", "TOKEN"])
    gr = group_by_prefix(result, prefixes=["DB"])
    assert gr.ungrouped[0].key in {"SECRET", "TOKEN"}
    assert len(gr.ungrouped) == 2


def test_mismatch_keys_are_grouped():
    result = _make_result(mismatches=[("AWS_REGION", "us-east-1", "eu-west-1")])
    gr = group_by_prefix(result)
    assert "AWS" in gr.groups
    assert gr.groups["AWS"].diffs[0].key == "AWS_REGION"


def test_total_diffs_counts_all_categories():
    result = _make_result(
        missing_right=["DB_HOST"],
        missing_left=["APP_PORT"],
        mismatches=[("AWS_KEY", "a", "b")],
    )
    gr = group_by_prefix(result)
    assert gr.total_diffs() == 3


def test_none_result_raises_group_error():
    with pytest.raises(GroupError):
        group_by_prefix(None)  # type: ignore[arg-type]


def test_empty_result_returns_empty_groups():
    result = _make_result()
    gr = group_by_prefix(result)
    assert gr.total_diffs() == 0
    assert gr.groups == {}
    assert gr.ungrouped == []


def test_group_names_are_sorted():
    result = _make_result(
        missing_right=["Z_KEY", "A_KEY", "M_KEY"]
    )
    gr = group_by_prefix(result)
    assert gr.group_names == sorted(gr.group_names)


def test_key_group_str():
    kg = KeyGroup(prefix="DB", diffs=[KeyDiff("DB_HOST", "a", "b")])
    assert "DB" in str(kg)
    assert "1" in str(kg)


def test_custom_separator():
    result = _make_result(missing_right=["DB.HOST", "DB.PORT"])
    gr = group_by_prefix(result, separator=".")
    assert "DB" in gr.groups
    assert len(gr.groups["DB"]) == 2


def test_prefix_shorter_than_min_length_is_ungrouped():
    # Single-char prefix 'X' should not form a group with default min_prefix_length=2
    result = _make_result(missing_right=["X_VAR"])
    gr = group_by_prefix(result, min_prefix_length=2)
    assert "X" not in gr.groups
    assert len(gr.ungrouped) == 1
