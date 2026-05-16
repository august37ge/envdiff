"""Tests for envdiff.differ_interactive."""
from __future__ import annotations

import pathlib
import pytest

from envdiff.differ_interactive import (
    InteractiveDiffError,
    SideBySideRow,
    SideBySideResult,
    build_side_by_side,
    diff_interactive,
)
from envdiff.comparator import CompareResult, KeyDiff


def _write(tmp_path: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# unit: build_side_by_side
# ---------------------------------------------------------------------------

def _make_compare_result(
    diffs=None, missing_left=None, missing_right=None
) -> CompareResult:
    return CompareResult(
        diffs=diffs or [],
        missing_in_left=missing_left or [],
        missing_in_right=missing_right or [],
    )


def test_build_raises_on_none_result():
    with pytest.raises(InteractiveDiffError):
        build_side_by_side(None, "a", "b")  # type: ignore[arg-type]


def test_build_no_diffs_returns_empty_rows():
    result = _make_compare_result()
    sbs = build_side_by_side(result, "a.env", "b.env")
    assert not sbs.has_diffs
    assert sbs.rows == []


def test_build_missing_right_row():
    result = _make_compare_result(missing_right=["DB_HOST"])
    sbs = build_side_by_side(result, "a.env", "b.env")
    assert sbs.has_diffs
    rows = sbs.rows_with_status("missing_right")
    assert len(rows) == 1
    assert rows[0].key == "DB_HOST"


def test_build_missing_left_row():
    result = _make_compare_result(missing_left=["SECRET"])
    sbs = build_side_by_side(result, "a.env", "b.env")
    rows = sbs.rows_with_status("missing_left")
    assert len(rows) == 1
    assert rows[0].key == "SECRET"


def test_build_mismatch_row():
    diff = KeyDiff(key="PORT", left_value="8080", right_value="9090")
    result = _make_compare_result(diffs=[diff])
    sbs = build_side_by_side(result, "a.env", "b.env")
    rows = sbs.rows_with_status("mismatch")
    assert len(rows) == 1
    assert rows[0].left_value == "8080"
    assert rows[0].right_value == "9090"


def test_side_by_side_row_str_contains_key():
    row = SideBySideRow(key="API_KEY", left_value="abc", right_value=None, status="missing_right")
    assert "API_KEY" in str(row)
    assert "<absent>" in str(row)


# ---------------------------------------------------------------------------
# integration: diff_interactive with real files
# ---------------------------------------------------------------------------

def test_diff_interactive_identical_files(tmp_path):
    left = _write(tmp_path, ".env.left", "KEY=value\nFOO=bar\n")
    right = _write(tmp_path, ".env.right", "KEY=value\nFOO=bar\n")
    sbs = diff_interactive(str(left), str(right))
    assert not sbs.has_diffs


def test_diff_interactive_missing_key(tmp_path):
    left = _write(tmp_path, ".env.left", "KEY=value\nEXTRA=yes\n")
    right = _write(tmp_path, ".env.right", "KEY=value\n")
    sbs = diff_interactive(str(left), str(right))
    assert sbs.has_diffs
    assert len(sbs.rows_with_status("missing_right")) == 1


def test_diff_interactive_bad_path_raises():
    with pytest.raises(InteractiveDiffError):
        diff_interactive("/no/such/file.env", "/also/missing.env")
