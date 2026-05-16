"""Tests for envdiff.annotator."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.annotator import (
    AnnotatorError,
    annotate_result,
    load_annotations,
)
from envdiff.comparator import CompareResult, KeyDiff


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _make_result(
    missing_right=(), missing_left=(), mismatched=()
) -> CompareResult:
    return CompareResult(
        missing_in_right=[KeyDiff(k, left_value=v) for k, v in missing_right],
        missing_in_left=[KeyDiff(k, right_value=v) for k, v in missing_left],
        mismatched=[
            KeyDiff(k, left_value=lv, right_value=rv)
            for k, lv, rv in mismatched
        ],
    )


# --- load_annotations ---

def test_load_annotations_basic(tmp_path):
    f = _write(tmp_path, "ann.env", 'DB_HOST = "primary database host"\n')
    ann = load_annotations(f)
    assert ann == {"DB_HOST": "primary database host"}


def test_load_annotations_ignores_comments_and_blanks(tmp_path):
    content = "# header\n\nAPI_KEY = 'secret key'\n"
    f = _write(tmp_path, "ann.env", content)
    ann = load_annotations(f)
    assert "API_KEY" in ann
    assert len(ann) == 1


def test_load_annotations_missing_file_raises(tmp_path):
    with pytest.raises(AnnotatorError, match="not found"):
        load_annotations(tmp_path / "missing.env")


def test_load_annotations_invalid_line_raises(tmp_path):
    f = _write(tmp_path, "ann.env", "BADLINE\n")
    with pytest.raises(AnnotatorError, match="Invalid annotation"):
        load_annotations(f)


def test_load_annotations_empty_key_raises(tmp_path):
    f = _write(tmp_path, "ann.env", ' = "oops"\n')
    with pytest.raises(AnnotatorError, match="Empty key"):
        load_annotations(f)


# --- annotate_result ---

def test_annotate_result_none_raises():
    with pytest.raises(AnnotatorError, match="None"):
        annotate_result(None, {})


def test_annotate_no_diffs_returns_empty():
    result = _make_result()
    ar = annotate_result(result, {"UNUSED": "note"})
    assert ar.total == 0
    assert ar.unannotated_count == 0


def test_annotate_attaches_annotation_to_matching_key():
    result = _make_result(missing_right=[("DB_HOST", "localhost")])
    ar = annotate_result(result, {"DB_HOST": "primary host"})
    assert ar.total == 1
    assert ar.annotated[0].annotation == "primary host"
    assert ar.unannotated_count == 0


def test_annotate_unannotated_count_increments_for_missing_note():
    result = _make_result(missing_right=[("DB_HOST", "localhost"), ("PORT", "5432")])
    ar = annotate_result(result, {"DB_HOST": "host note"})
    assert ar.unannotated_count == 1


def test_annotated_key_str_includes_annotation():
    result = _make_result(missing_right=[("API_URL", "https://example.com")])
    ar = annotate_result(result, {"API_URL": "base API endpoint"})
    rendered = str(ar.annotated[0])
    assert "API_URL" in rendered
    assert "base API endpoint" in rendered


def test_annotated_key_str_without_annotation_has_no_hash():
    result = _make_result(missing_right=[("PLAIN_KEY", "val")])
    ar = annotate_result(result, {})
    rendered = str(ar.annotated[0])
    assert "#" not in rendered
