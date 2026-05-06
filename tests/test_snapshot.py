"""Tests for envdiff.snapshot — save/load CompareResult snapshots."""

import json
import os

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.snapshot import SnapshotError, load_snapshot, save_snapshot


@pytest.fixture()
def simple_result() -> CompareResult:
    return CompareResult(
        missing_in_left={"ONLY_RIGHT"},
        missing_in_right={"ONLY_LEFT"},
        mismatched=[
            KeyDiff(key="DB_HOST", left_value="localhost", right_value="prod.db")
        ],
    )


@pytest.fixture()
def clean_result() -> CompareResult:
    return CompareResult(missing_in_left=set(), missing_in_right=set(), mismatched=[])


def test_save_creates_file(tmp_path, simple_result):
    out = str(tmp_path / "snap.json")
    save_snapshot(simple_result, out, left_name="dev", right_name="prod")
    assert os.path.isfile(out)


def test_save_json_structure(tmp_path, simple_result):
    out = str(tmp_path / "snap.json")
    save_snapshot(simple_result, out, left_name="dev", right_name="prod")
    with open(out) as fh:
        data = json.load(fh)
    assert data["left"] == "dev"
    assert data["right"] == "prod"
    assert "ONLY_RIGHT" in data["missing_in_left"]
    assert "ONLY_LEFT" in data["missing_in_right"]
    assert len(data["mismatched"]) == 1
    assert data["mismatched"][0]["key"] == "DB_HOST"
    assert "created_at" in data


def test_load_roundtrip(tmp_path, simple_result):
    out = str(tmp_path / "snap.json")
    save_snapshot(simple_result, out, left_name="staging", right_name="prod")
    loaded, meta = load_snapshot(out)

    assert loaded.missing_in_left == simple_result.missing_in_left
    assert loaded.missing_in_right == simple_result.missing_in_right
    assert len(loaded.mismatched) == 1
    assert loaded.mismatched[0].key == "DB_HOST"
    assert meta["left"] == "staging"
    assert meta["right"] == "prod"
    assert meta["created_at"] is not None


def test_load_clean_result(tmp_path, clean_result):
    out = str(tmp_path / "clean.json")
    save_snapshot(clean_result, out)
    loaded, _ = load_snapshot(out)
    assert not loaded.has_diffs()


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(str(tmp_path / "nonexistent.json"))


def test_load_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json{{{")
    with pytest.raises(SnapshotError, match="Cannot read"):
        load_snapshot(str(bad))


def test_save_bad_path_raises(simple_result):
    with pytest.raises(SnapshotError, match="Cannot write"):
        save_snapshot(simple_result, "/nonexistent_dir/snap.json")
