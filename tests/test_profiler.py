"""Tests for envdiff.profiler."""
from pathlib import Path

import pytest

from envdiff.profiler import profile_file, ProfileError


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_empty_file_returns_zero_counts(tmp_path):
    f = _write(tmp_path, ".env", "")
    result = profile_file(f)
    assert result.total_keys == 0
    assert result.avg_value_length == 0.0
    assert result.max_value_length == 0
    assert result.min_value_length == 0


def test_total_keys_counted(tmp_path):
    f = _write(tmp_path, ".env", "A=1\nB=2\nC=3\n")
    result = profile_file(f)
    assert result.total_keys == 3


def test_empty_value_detected(tmp_path):
    f = _write(tmp_path, ".env", "A=\nB=hello\n")
    result = profile_file(f)
    assert result.empty_values == 1


def test_numeric_value_detected(tmp_path):
    f = _write(tmp_path, ".env", "PORT=8080\nHOST=localhost\n")
    result = profile_file(f)
    assert result.numeric_values == 1


def test_boolean_value_detected(tmp_path):
    f = _write(tmp_path, ".env", "DEBUG=true\nVERBOSE=false\nNAME=app\n")
    result = profile_file(f)
    assert result.boolean_values == 2


def test_secret_like_key_detected(tmp_path):
    f = _write(tmp_path, ".env", "API_SECRET=abc123\nDB_PASSWORD=hunter2\nNAME=app\n")
    result = profile_file(f)
    assert result.secret_like_keys == 2


def test_other_category_is_remainder(tmp_path):
    f = _write(tmp_path, ".env", "NAME=myapp\nENV=production\n")
    result = profile_file(f)
    assert result.other_values == 2
    assert result.empty_values == 0
    assert result.numeric_values == 0
    assert result.boolean_values == 0
    assert result.secret_like_keys == 0


def test_avg_value_length(tmp_path):
    # values: "ab" (2), "abcd" (4) → avg 3.0
    f = _write(tmp_path, ".env", "A=ab\nB=abcd\n")
    result = profile_file(f)
    assert result.avg_value_length == pytest.approx(3.0)


def test_max_min_value_length(tmp_path):
    f = _write(tmp_path, ".env", "A=x\nB=hello\nC=hi\n")
    result = profile_file(f)
    assert result.max_value_length == 5
    assert result.min_value_length == 1


def test_comments_and_blanks_ignored(tmp_path):
    content = "# comment\n\nA=1\nB=2\n"
    f = _write(tmp_path, ".env", content)
    result = profile_file(f)
    assert result.total_keys == 2


def test_path_stored_in_profile(tmp_path):
    f = _write(tmp_path, ".env", "X=1\n")
    result = profile_file(f)
    assert str(f) == result.path


def test_profile_error_on_missing_file(tmp_path):
    with pytest.raises(ProfileError):
        profile_file(tmp_path / "nonexistent.env")


def test_category_counts_dict(tmp_path):
    f = _write(tmp_path, ".env", "A=1\nB=true\nC=\n")
    result = profile_file(f)
    assert result.category_counts.get("numeric") == 1
    assert result.category_counts.get("boolean") == 1
    assert result.category_counts.get("empty") == 1
