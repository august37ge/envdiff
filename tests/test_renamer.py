"""Tests for envdiff.renamer."""
from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.renamer import RenameError, RenameResult, detect_renames, _similarity


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_result(
    missing_in_right=(),
    missing_in_left=(),
    mismatches=(),
) -> CompareResult:
    diffs = []
    for k in missing_in_right:
        diffs.append(KeyDiff(key=k, left_value="val", right_value=None))
    for k in missing_in_left:
        diffs.append(KeyDiff(key=k, left_value=None, right_value="val"))
    for k, lv, rv in mismatches:
        diffs.append(KeyDiff(key=k, left_value=lv, right_value=rv))
    return CompareResult(diffs=diffs)


# ---------------------------------------------------------------------------
# _similarity unit tests
# ---------------------------------------------------------------------------

def test_similarity_identical():
    assert _similarity("DATABASE_URL", "DATABASE_URL") == 1.0


def test_similarity_completely_different():
    score = _similarity("AB", "XY")
    assert score == 0.0


def test_similarity_partial():
    score = _similarity("DB_HOST", "DATABASE_HOST")
    assert 0.0 < score < 1.0


# ---------------------------------------------------------------------------
# detect_renames
# ---------------------------------------------------------------------------

def test_none_result_raises():
    with pytest.raises(RenameError):
        detect_renames(None)  # type: ignore[arg-type]


def test_no_missing_keys_no_candidates():
    result = _make_result()
    rr = detect_renames(result)
    assert not rr.has_candidates
    assert rr.unmatched_left == []
    assert rr.unmatched_right == []


def test_obvious_rename_detected():
    # DB_HOST -> DATABASE_HOST is a plausible rename
    result = _make_result(
        missing_in_right=["DB_HOST"],
        missing_in_left=["DATABASE_HOST"],
    )
    rr = detect_renames(result, threshold=0.3)
    assert rr.has_candidates
    assert rr.candidates[0].left_key == "DB_HOST"
    assert rr.candidates[0].right_key == "DATABASE_HOST"
    assert 0.0 < rr.candidates[0].confidence <= 1.0


def test_unrelated_keys_not_matched():
    result = _make_result(
        missing_in_right=["ALPHA"],
        missing_in_left=["ZZZZ"],
    )
    rr = detect_renames(result, threshold=0.5)
    assert not rr.has_candidates
    assert "ALPHA" in rr.unmatched_left
    assert "ZZZZ" in rr.unmatched_right


def test_each_key_matched_at_most_once():
    # Two left keys both similar to one right key; only best match taken.
    result = _make_result(
        missing_in_right=["SECRET_KEY", "SECRET_KEYS"],
        missing_in_left=["SECRET_KEY_VALUE"],
    )
    rr = detect_renames(result, threshold=0.3)
    right_keys_used = [c.right_key for c in rr.candidates]
    assert right_keys_used.count("SECRET_KEY_VALUE") <= 1


def test_mismatches_do_not_affect_rename_detection():
    result = _make_result(
        missing_in_right=["OLD_NAME"],
        missing_in_left=["NEW_NAME"],
        mismatches=[("SHARED", "foo", "bar")],
    )
    rr = detect_renames(result, threshold=0.2)
    # SHARED should not appear in rename candidates
    keys = {c.left_key for c in rr.candidates} | {c.right_key for c in rr.candidates}
    assert "SHARED" not in keys


def test_threshold_zero_matches_everything():
    result = _make_result(
        missing_in_right=["A"],
        missing_in_left=["B"],
    )
    rr = detect_renames(result, threshold=0.0)
    assert rr.has_candidates
