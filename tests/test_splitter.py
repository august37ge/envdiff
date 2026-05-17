"""Tests for envdiff.splitter."""
from __future__ import annotations

import pathlib

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.splitter import SplitError, split_result


def _kd(key: str, left=None, right=None) -> KeyDiff:
    return KeyDiff(key=key, left_value=left, right_value=right)


def _make_result(*diffs: KeyDiff) -> CompareResult:
    missing_right = [d for d in diffs if d.right_value is None and d.left_value is not None]
    missing_left = [d for d in diffs if d.left_value is None and d.right_value is not None]
    mismatched = [d for d in diffs if d.left_value is not None and d.right_value is not None]
    return CompareResult(
        missing_in_right=missing_right,
        missing_in_left=missing_left,
        mismatched=mismatched,
    )


def test_none_result_raises():
    with pytest.raises(SplitError):
        split_result(None, ["DB"])


def test_empty_prefixes_raises():
    result = _make_result(_kd("DB_HOST", left="localhost"))
    with pytest.raises(SplitError):
        split_result(result, [])


def test_single_prefix_captures_matching_keys():
    diffs = [_kd("DB_HOST", left="a"), _kd("DB_PORT", left="5432"), _kd("APP_NAME", left="x")]
    sr = split_result(_make_result(*diffs), ["DB"])
    assert len(sr.buckets["DB"]) == 2
    assert len(sr.remainder) == 1
    assert sr.remainder.diffs[0].key == "APP_NAME"


def test_multiple_prefixes_first_match_wins():
    diffs = [_kd("AWS_KEY", left="k"), _kd("AWS_SECRET", left="s"), _kd("DB_URL", left="u")]
    sr = split_result(_make_result(*diffs), ["AWS", "DB"])
    assert len(sr.buckets["AWS"]) == 2
    assert len(sr.buckets["DB"]) == 1
    assert not sr.remainder.has_diffs


def test_remainder_contains_unmatched():
    diffs = [_kd("REDIS_URL", left="r"), _kd("DB_HOST", left="h")]
    sr = split_result(_make_result(*diffs), ["DB"])
    assert sr.remainder.diffs[0].key == "REDIS_URL"


def test_glob_mode_matches_pattern():
    diffs = [_kd("AWS_ACCESS_KEY_ID", left="a"), _kd("DB_HOST", left="h")]
    sr = split_result(_make_result(*diffs), ["AWS_*"], use_glob=True)
    assert len(sr.buckets["AWS_*"]) == 1
    assert sr.buckets["AWS_*"].diffs[0].key == "AWS_ACCESS_KEY_ID"
    assert len(sr.remainder) == 1


def test_any_diffs_true_when_buckets_have_content():
    diffs = [_kd("DB_HOST", left="a")]
    sr = split_result(_make_result(*diffs), ["DB"])
    assert sr.any_diffs is True


def test_any_diffs_false_when_no_diffs():
    sr = split_result(_make_result(), ["DB"])
    assert sr.any_diffs is False


def test_bucket_names_returns_ordered_list():
    sr = split_result(_make_result(), ["AWS", "DB", "APP"])
    assert sr.bucket_names() == ["AWS", "DB", "APP"]


def test_exact_key_match_without_separator():
    """A key equal to the prefix itself (no separator) should still match."""
    diffs = [_kd("DB", left="sqlite")]
    sr = split_result(_make_result(*diffs), ["DB"])
    assert len(sr.buckets["DB"]) == 1


def test_custom_separator_respected():
    diffs = [_kd("DB.HOST", left="h"), _kd("DB_HOST", left="h2")]
    sr = split_result(_make_result(*diffs), ["DB"], separator=".")
    assert len(sr.buckets["DB"]) == 1
    assert sr.buckets["DB"].diffs[0].key == "DB.HOST"
    assert len(sr.remainder) == 1
