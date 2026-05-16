"""Tests for envdiff.scheduler_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.scheduler_cli import add_scheduler_subcommands


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_left(tmp_path: Path) -> Path:
    return _write(tmp_path / "left.env", "FOO=bar\nSHARED=same\n")


@pytest.fixture()
def env_right(tmp_path: Path) -> Path:
    return _write(tmp_path / "right.env", "BAZ=qux\nSHARED=same\n")


def _make_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_scheduler_subcommands(sub)
    return parser.parse_args(argv)


def test_schedule_run_exits_zero(tmp_path, env_left, env_right):
    log_path = str(tmp_path / "log.json")
    args = _make_args(["schedule-run", str(env_left), str(env_right), "--log", log_path])
    rc = args.func(args)
    assert rc == 0


def test_schedule_run_creates_log(tmp_path, env_left, env_right):
    log_path = tmp_path / "log.json"
    args = _make_args(["schedule-run", str(env_left), str(env_right), "--log", str(log_path)])
    args.func(args)
    assert log_path.exists()
    data = json.loads(log_path.read_text())
    assert len(data["entries"]) == 1


def test_schedule_run_fail_on_diffs(tmp_path, env_left, env_right):
    log_path = str(tmp_path / "log.json")
    args = _make_args(
        ["schedule-run", str(env_left), str(env_right), "--log", log_path, "--fail-on-diffs"]
    )
    rc = args.func(args)
    # left has FOO, right has BAZ – diffs exist
    assert rc == 1


def test_schedule_run_missing_file_returns_error(tmp_path):
    log_path = str(tmp_path / "log.json")
    args = _make_args(["schedule-run", "no_such.env", "also_none.env", "--log", log_path])
    rc = args.func(args)
    assert rc == 1


def test_schedule_log_displays_entries(tmp_path, env_left, env_right, capsys):
    log_path = str(tmp_path / "log.json")
    run_args = _make_args(["schedule-run", str(env_left), str(env_right), "--log", log_path])
    run_args.func(run_args)

    log_args = _make_args(["schedule-log", "--log", log_path])
    rc = log_args.func(log_args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "left.env" in out


def test_schedule_log_missing_log_returns_error(tmp_path):
    log_path = str(tmp_path / "nonexistent.json")
    args = _make_args(["schedule-log", "--log", log_path])
    rc = args.func(args)
    assert rc == 1
