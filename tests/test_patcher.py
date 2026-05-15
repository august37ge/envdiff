"""Tests for envdiff.patcher."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.differ import diff_files
from envdiff.patcher import (
    PatchError,
    PatchOptions,
    PatchResult,
    patch_result,
    write_patch,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_fill_missing_adds_keys(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=1\nBAR=2\n")
    other = _write(tmp_path, "other.env", "FOO=1\nBAR=2\nBAZ=3\n")
    compare = diff_files(base, other)
    result = patch_result(base, other, compare)
    assert "BAZ" in result.patched
    assert result.patched["BAZ"] == "3"
    assert "BAZ" in result.added_keys


def test_no_fill_missing_leaves_keys_absent(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=1\n")
    other = _write(tmp_path, "other.env", "FOO=1\nEXTRA=hello\n")
    compare = diff_files(base, other)
    opts = PatchOptions(fill_missing=False)
    result = patch_result(base, other, compare, opts)
    assert "EXTRA" not in result.patched
    assert result.added_keys == []


def test_overwrite_mismatches_updates_value(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=old\n")
    other = _write(tmp_path, "other.env", "FOO=new\n")
    compare = diff_files(base, other)
    opts = PatchOptions(overwrite_mismatches=True)
    result = patch_result(base, other, compare, opts)
    assert result.patched["FOO"] == "new"
    assert "FOO" in result.changed_keys


def test_no_overwrite_mismatches_keeps_base_value(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=old\n")
    other = _write(tmp_path, "other.env", "FOO=new\n")
    compare = diff_files(base, other)
    opts = PatchOptions(overwrite_mismatches=False)
    result = patch_result(base, other, compare, opts)
    assert result.patched["FOO"] == "old"
    assert result.changed_keys == []


def test_identical_files_no_changes(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=1\nBAR=2\n")
    other = _write(tmp_path, "other.env", "FOO=1\nBAR=2\n")
    compare = diff_files(base, other)
    result = patch_result(base, other, compare)
    assert not result.has_changes


def test_write_patch_creates_file(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=1\n")
    other = _write(tmp_path, "other.env", "FOO=1\nBAR=2\n")
    compare = diff_files(base, other)
    result = patch_result(base, other, compare)
    dest = tmp_path / "out.env"
    write_patch(result, dest)
    content = dest.read_text()
    assert "FOO=1" in content
    assert "BAR=2" in content


def test_write_patch_with_comment_source(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=1\n")
    other = _write(tmp_path, "other.env", "FOO=1\nNEW=yes\n")
    compare = diff_files(base, other)
    opts = PatchOptions(comment_source=True)
    result = patch_result(base, other, compare, opts)
    dest = tmp_path / "out.env"
    write_patch(result, dest, opts)
    content = dest.read_text()
    assert "# added by envdiff patcher" in content


def test_write_patch_bad_path_raises(tmp_path: Path) -> None:
    base = _write(tmp_path, "base.env", "FOO=1\n")
    other = _write(tmp_path, "other.env", "FOO=1\nBAR=2\n")
    compare = diff_files(base, other)
    result = patch_result(base, other, compare)
    bad_dest = tmp_path / "no_such_dir" / "out.env"
    with pytest.raises(PatchError):
        write_patch(result, bad_dest)
