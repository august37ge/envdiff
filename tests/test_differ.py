"""Tests for envdiff.differ — high-level diff orchestration."""

import pytest
from pathlib import Path

from envdiff.differ import diff_files, DiffError


@pytest.fixture()
def write_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _write


def test_identical_files_no_diffs(write_env):
    left = write_env("left.env", "FOO=bar\nBAZ=qux\n")
    right = write_env("right.env", "FOO=bar\nBAZ=qux\n")
    result = diff_files(left, right)
    assert not result.has_diffs


def test_missing_key_in_right(write_env):
    left = write_env("left.env", "FOO=bar\nEXTRA=1\n")
    right = write_env("right.env", "FOO=bar\n")
    result = diff_files(left, right)
    assert "EXTRA" in result.missing_in_right


def test_missing_key_in_left(write_env):
    left = write_env("left.env", "FOO=bar\n")
    right = write_env("right.env", "FOO=bar\nNEW_KEY=hello\n")
    result = diff_files(left, right)
    assert "NEW_KEY" in result.missing_in_left


def test_value_mismatch_detected(write_env):
    left = write_env("left.env", "FOO=bar\n")
    right = write_env("right.env", "FOO=different\n")
    result = diff_files(left, right)
    assert any(d.key == "FOO" for d in result.mismatches)


def test_keys_only_ignores_value_diff(write_env):
    left = write_env("left.env", "FOO=bar\n")
    right = write_env("right.env", "FOO=different\n")
    result = diff_files(left, right, keys_only=True)
    assert not result.has_diffs


def test_missing_file_raises_diff_error(tmp_path, write_env):
    left = write_env("left.env", "FOO=bar\n")
    right = tmp_path / "nonexistent.env"
    with pytest.raises(DiffError, match="File not found"):
        diff_files(left, right)


def test_validate_flag_raises_on_bad_file(write_env):
    left = write_env("left.env", "FOO=bar\n")
    # Missing '=' makes this line invalid
    right = write_env("right.env", "BADLINE\n")
    with pytest.raises(DiffError, match="Validation failed"):
        diff_files(left, right, validate=True)


def test_validate_flag_passes_on_good_files(write_env):
    left = write_env("left.env", "FOO=bar\n")
    right = write_env("right.env", "FOO=baz\n")
    # Should not raise
    result = diff_files(left, right, validate=True)
    assert result is not None
