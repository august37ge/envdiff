"""Tests for envdiff.exporter."""

from __future__ import annotations

import os
import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.exporter import ExportError, export_result, write_export


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def result_with_diffs() -> CompareResult:
    return CompareResult(
        left={"A": "1", "B": "2", "C": "old"},
        right={"B": "2", "C": "new", "D": "4"},
        missing_in_right=["A"],
        missing_in_left=["D"],
        value_diffs=[KeyDiff(key="C", left_value="old", right_value="new")],
    )


@pytest.fixture()
def result_no_diffs() -> CompareResult:
    return CompareResult(
        left={"X": "1"},
        right={"X": "1"},
        missing_in_right=[],
        missing_in_left=[],
        value_diffs=[],
    )


# ---------------------------------------------------------------------------
# CSV tests
# ---------------------------------------------------------------------------

def test_csv_contains_header(result_with_diffs):
    out = export_result(result_with_diffs, "csv")
    assert out.startswith("key,status,left_value,right_value")


def test_csv_missing_in_right(result_with_diffs):
    out = export_result(result_with_diffs, "csv")
    assert "A,missing_in_right" in out


def test_csv_missing_in_left(result_with_diffs):
    out = export_result(result_with_diffs, "csv")
    assert "D,missing_in_left" in out


def test_csv_value_mismatch(result_with_diffs):
    out = export_result(result_with_diffs, "csv")
    assert "C,value_mismatch,old,new" in out


def test_csv_no_diffs_only_header(result_no_diffs):
    out = export_result(result_no_diffs, "csv")
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 1  # header only


# ---------------------------------------------------------------------------
# Markdown tests
# ---------------------------------------------------------------------------

def test_markdown_header(result_with_diffs):
    out = export_result(result_with_diffs, "markdown")
    assert out.startswith("# envdiff Report")


def test_markdown_table_row_mismatch(result_with_diffs):
    out = export_result(result_with_diffs, "markdown")
    assert "`C`" in out and "value mismatch" in out


def test_markdown_no_diffs_message(result_no_diffs):
    out = export_result(result_no_diffs, "markdown")
    assert "No differences found" in out
    assert "|" not in out


# ---------------------------------------------------------------------------
# Unsupported format
# ---------------------------------------------------------------------------

def test_unsupported_format_raises(result_with_diffs):
    with pytest.raises(ExportError, match="Unsupported export format"):
        export_result(result_with_diffs, "xml")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# write_export
# ---------------------------------------------------------------------------

def test_write_export_creates_file(tmp_path, result_with_diffs):
    dest = tmp_path / "report.csv"
    write_export(result_with_diffs, "csv", str(dest))
    assert dest.exists()
    assert "key,status" in dest.read_text()


def test_write_export_bad_path_raises(result_with_diffs):
    with pytest.raises(ExportError, match="Cannot write export file"):
        write_export(result_with_diffs, "csv", "/nonexistent_dir/out.csv")
