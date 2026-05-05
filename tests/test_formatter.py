"""Tests for envdiff.formatter."""

import json
import pytest
from envdiff.comparator import compare_envs
from envdiff.formatter import format_result


LEFT = {"DB_HOST": "localhost", "SECRET": "abc"}
RIGHT = {"DB_HOST": "prod.db", "API_KEY": "xyz"}


@pytest.fixture
def result_with_diffs():
    return compare_envs(LEFT, RIGHT, left_path=".env.dev", right_path=".env.prod")


@pytest.fixture
def result_no_diffs():
    return compare_envs({"A": "1"}, {"A": "1"}, left_path="a", right_path="b")


def test_text_format_header(result_with_diffs):
    out = format_result(result_with_diffs, fmt="text")
    assert ".env.dev" in out
    assert ".env.prod" in out


def test_text_format_no_diffs(result_no_diffs):
    out = format_result(result_no_diffs, fmt="text")
    assert "No differences" in out


def test_text_format_shows_keys(result_with_diffs):
    out = format_result(result_with_diffs, fmt="text")
    assert "SECRET" in out
    assert "API_KEY" in out
    assert "DB_HOST" in out


def test_summary_no_diffs(result_no_diffs):
    out = format_result(result_no_diffs, fmt="summary")
    assert out.startswith("OK")


def test_summary_with_diffs(result_with_diffs):
    out = format_result(result_with_diffs, fmt="summary")
    assert "difference" in out


def test_json_format_valid_json(result_with_diffs):
    out = format_result(result_with_diffs, fmt="json")
    data = json.loads(out)
    assert data["left"] == ".env.dev"
    assert data["right"] == ".env.prod"
    assert isinstance(data["diffs"], list)


def test_json_format_diff_fields(result_with_diffs):
    out = format_result(result_with_diffs, fmt="json")
    data = json.loads(out)
    for diff in data["diffs"]:
        assert "key" in diff
        assert "status" in diff
        assert "left_value" in diff
        assert "right_value" in diff


def test_json_format_no_diffs(result_no_diffs):
    out = format_result(result_no_diffs, fmt="json")
    data = json.loads(out)
    assert data["diffs"] == []
