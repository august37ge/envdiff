"""Tests for envdiff.reporter module."""

import json
import os
import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.reporter import ReportOptions, generate_report, write_report


@pytest.fixture
def simple_result():
    return CompareResult(
        left_file=".env.dev",
        right_file=".env.prod",
        missing_in_left=["PROD_ONLY_KEY"],
        missing_in_right=["DEV_ONLY_KEY"],
        value_mismatches=[
            KeyDiff(key="DATABASE_URL", left_value="sqlite://", right_value="postgres://")
        ],
    )


@pytest.fixture
def clean_result():
    return CompareResult(
        left_file=".env.a",
        right_file=".env.b",
        missing_in_left=[],
        missing_in_right=[],
        value_mismatches=[],
    )


def test_generate_report_text(simple_result):
    opts = ReportOptions(format="text")
    report = generate_report(simple_result, opts)
    assert "DEV_ONLY_KEY" in report
    assert "PROD_ONLY_KEY" in report
    assert "DATABASE_URL" in report


def test_generate_report_json(simple_result):
    opts = ReportOptions(format="json")
    report = generate_report(simple_result, opts)
    data = json.loads(report)
    assert "missing_in_left" in data
    assert "PROD_ONLY_KEY" in data["missing_in_left"]


def test_generate_report_summary_only(simple_result):
    opts = ReportOptions(summary_only=True)
    report = generate_report(simple_result, opts)
    assert "Missing in left:  1" in report
    assert "Missing in right: 1" in report
    assert "Value mismatches: 1" in report
    assert "Total issues:     3" in report


def test_summary_no_diffs(clean_result):
    opts = ReportOptions(summary_only=True)
    report = generate_report(clean_result, opts)
    assert "Total issues:     0" in report


def test_write_report_to_file(tmp_path, simple_result):
    out = tmp_path / "report.txt"
    opts = ReportOptions(format="text", output_file=str(out))
    write_report(simple_result, opts)
    assert out.exists()
    content = out.read_text()
    assert "DATABASE_URL" in content


def test_write_report_stdout(capsys, simple_result):
    opts = ReportOptions(format="text")
    write_report(simple_result, opts)
    captured = capsys.readouterr()
    assert "DEV_ONLY_KEY" in captured.out
