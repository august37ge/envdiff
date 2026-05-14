"""Tests for envdiff.scorer."""
import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.scorer import ScoreError, ScoreResult, score_result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(
    missing_left=(),
    missing_right=(),
    mismatches=(),
    total: int = 0,
) -> CompareResult:
    """Build a minimal CompareResult for testing."""
    ml = [KeyDiff(key=k, left_value=None, right_value="x") for k in missing_left]
    mr = [KeyDiff(key=k, left_value="x", right_value=None) for k in missing_right]
    mm = [KeyDiff(key=k, left_value="a", right_value="b") for k in mismatches]
    cr = CompareResult(missing_in_left=ml, missing_in_right=mr, value_mismatches=mm)
    # Patch total_keys so scorer can use it.
    all_keys = set(missing_left) | set(missing_right) | set(mismatches)
    cr.total_keys = total or len(all_keys)  # type: ignore[attr-defined]
    cr.matched_count = max(0, cr.total_keys - len(ml) - len(mr) - len(mm))  # type: ignore[attr-defined]
    return cr


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_perfect_score_no_diffs():
    result = _make_result(total=5)
    sr = score_result(result)
    assert sr.score == 100.0
    assert sr.grade == "A"
    assert sr.matched_keys == 5


def test_all_missing_in_right():
    result = _make_result(missing_right=["A", "B", "C", "D"], total=4)
    sr = score_result(result)
    assert sr.score == 0.0
    assert sr.grade == "D"
    assert sr.missing_in_right == 4


def test_partial_missing_reduces_score():
    result = _make_result(missing_right=["KEY1"], total=4)
    sr = score_result(result)
    assert 0.0 < sr.score < 100.0


def test_mismatch_penalty_lower_than_missing():
    result_miss = _make_result(missing_right=["K"], total=2)
    result_mm = _make_result(mismatches=["K"], total=2)
    sr_miss = score_result(result_miss)
    sr_mm = score_result(result_mm)
    # Missing key should hurt more than a value mismatch (default weights).
    assert sr_miss.score <= sr_mm.score


def test_grade_boundaries():
    def _sr(score: float) -> ScoreResult:
        return ScoreResult(
            total_keys=10, matched_keys=0,
            missing_in_left=0, missing_in_right=0,
            mismatched_values=0, score=score,
        )

    assert _sr(95.0).grade == "A"
    assert _sr(80.0).grade == "B"
    assert _sr(60.0).grade == "C"
    assert _sr(30.0).grade == "D"


def test_negative_weight_raises():
    result = _make_result(total=2)
    with pytest.raises(ScoreError):
        score_result(result, weight_missing=-1.0)


def test_custom_weights_affect_score():
    result = _make_result(mismatches=["X"], total=4)
    sr_low = score_result(result, weight_mismatch=0.1)
    sr_high = score_result(result, weight_mismatch=1.0)
    assert sr_low.score >= sr_high.score


def test_str_representation():
    result = _make_result(missing_right=["FOO"], total=3)
    sr = score_result(result)
    text = str(sr)
    assert "Score" in text
    assert "Grade" in text
