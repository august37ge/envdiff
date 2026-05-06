"""Tests for snapshot CLI sub-commands."""

import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.snapshot_cli import _cmd_load_snapshot, _cmd_save_snapshot


def _write(path: Path, content: str) -> str:
    path.write_text(content)
    return str(path)


@pytest.fixture()
def env_left(tmp_path):
    return _write(tmp_path / ".env.left", "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")


@pytest.fixture()
def env_right(tmp_path):
    return _write(tmp_path / ".env.right", "DB_HOST=prod.db\nDB_PORT=5432\nNEW_KEY=1\n")


def test_save_snapshot_creates_file(tmp_path, env_left, env_right):
    out = str(tmp_path / "snap.json")
    args = Namespace(left=env_left, right=env_right, output=out)
    code = _cmd_save_snapshot(args)
    assert code == 0
    assert Path(out).is_file()
    data = json.loads(Path(out).read_text())
    assert data["left"] == env_left
    assert data["right"] == env_right


def test_save_snapshot_bad_output(tmp_path, env_left, env_right, capsys):
    args = Namespace(
        left=env_left, right=env_right, output="/no_such_dir/snap.json"
    )
    code = _cmd_save_snapshot(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "Cannot write" in captured.err


def test_save_snapshot_bad_left(tmp_path, env_right, capsys):
    args = Namespace(
        left=str(tmp_path / "missing.env"), right=env_right, output=str(tmp_path / "s.json")
    )
    code = _cmd_save_snapshot(args)
    assert code == 1


def test_load_snapshot_text(tmp_path, env_left, env_right, capsys):
    snap = str(tmp_path / "snap.json")
    _cmd_save_snapshot(Namespace(left=env_left, right=env_right, output=snap))
    args = Namespace(snapshot=snap, fmt="text")
    code = _cmd_load_snapshot(args)
    captured = capsys.readouterr()
    assert "Snapshot from" in captured.out
    # diffs exist so exit code should be 1
    assert code == 1


def test_load_snapshot_missing_file(tmp_path, capsys):
    args = Namespace(snapshot=str(tmp_path / "nope.json"), fmt="text")
    code = _cmd_load_snapshot(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_load_snapshot_no_diffs_returns_zero(tmp_path):
    left = _write(tmp_path / "a.env", "KEY=value\n")
    right = _write(tmp_path / "b.env", "KEY=value\n")
    snap = str(tmp_path / "snap.json")
    _cmd_save_snapshot(Namespace(left=left, right=right, output=snap))
    args = Namespace(snapshot=snap, fmt="summary")
    code = _cmd_load_snapshot(args)
    assert code == 0
