"""Tests for envdiff.summarizer."""

import json
import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.summarizer import SummaryError, SummaryReport, summarize, format_summary


def _make_result(
    missing_left: list[str] = (),
    missing_right: list[str] = (),
    mismatches: list[tuple[str, str, str]] = (),
) -> CompareResult:
    diffs = []
    for k in missing_left:
        diffs.append(KeyDiff(key=k, left_value=None, right_value="val"))
    for k in missing_right:
        diffs.append(KeyDiff(key=k, left_value="val", right_value=None))
    for k, lv, rv in mismatches:
        diffs.append(KeyDiff(key=k, left_value=lv, right_value=rv))
    return CompareResult(diffs=diffs)


def test_summarize_no_diffs():
    result = _make_result()
    report = summarize(result)
    assert report.total_keys == 0
    assert report.missing_in_left == 0
    assert report.missing_in_right == 0
    assert report.mismatches == 0
    assert report.health == "healthy"
    assert report.score.score == 100.0


def test_summarize_missing_in_right():
    result = _make_result(missing_right=["KEY_A", "KEY_B"])
    report = summarize(result)
    assert report.missing_in_right == 2
    assert report.total_keys == 2


def test_summarize_missing_in_left():
    result = _make_result(missing_left=["KEY_X"])
    report = summarize(result)
    assert report.missing_in_left == 1


def test_summarize_mismatches():
    result = _make_result(mismatches=[("DB_URL", "old", "new")])
    report = summarize(result)
    assert report.mismatches == 1


def test_health_warning():
    result = _make_result(
        missing_right=[f"K{i}" for i in range(5)],
        mismatches=[(f"M{i}", "a", "b") for i in range(5)],
    )
    report = summarize(result)
    assert report.health in ("warning", "critical")


def test_health_critical():
    result = _make_result(
        missing_right=[f"K{i}" for i in range(20)],
    )
    report = summarize(result)
    assert report.health == "critical"


def test_format_summary_text():
    result = _make_result(missing_right=["FOO"])
    report = summarize(result)
    text = format_summary(report, fmt="text")
    assert "Health" in text
    assert "Score" in text
    assert "Missing in right" in text


def test_format_summary_json():
    result = _make_result(mismatches=[("X", "1", "2")])
    report = summarize(result)
    raw = format_summary(report, fmt="json")
    data = json.loads(raw)
    assert "health" in data
    assert "score" in data
    assert "mismatches" in data
    assert data["mismatches"] == 1


def test_format_summary_unknown_format_raises():
    result = _make_result()
    report = summarize(result)
    with pytest.raises(SummaryError, match="Unknown format"):
        format_summary(report, fmt="xml")


def test_summarize_none_raises():
    with pytest.raises((SummaryError, AttributeError)):
        summarize(None)  # type: ignore


def test_str_representation():
    result = _make_result(missing_left=["A"], missing_right=["B"])
    report = summarize(result)
    s = str(report)
    assert "HEALTHY" in s.upper() or "WARNING" in s.upper() or "CRITICAL" in s.upper()
