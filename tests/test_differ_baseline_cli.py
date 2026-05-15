"""Tests for envdiff.differ_baseline_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.differ_baseline_cli import add_baseline_subcommands


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _write_snapshot(path: Path, left: dict[str, str]) -> Path:
    path.write_text(json.dumps({"left": left, "right": {}, "diffs": []}))
    return path


def _make_args(tmp_path: Path, env_content: str, snap_left: dict[str, str], **kwargs):
    env = _write(tmp_path / ".env", env_content)
    snap = _write_snapshot(tmp_path / "snap.json", snap_left)
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_baseline_subcommands(sub)
    base_args = ["baseline", str(env), str(snap)]
    for flag, val in kwargs.items():
        if val is True:
            base_args.append(f"--{flag.replace('_', '-')}")
        elif val is not False:
            base_args += [f"--{flag.replace('_', '-')}", str(val)]
    return parser.parse_args(base_args)


def test_baseline_exits_zero_on_sync(tmp_path):
    args = _make_args(tmp_path, "A=1\n", {"A": "1"})
    assert args.func(args) == 0


def test_baseline_exits_zero_with_diffs_no_fail_flag(tmp_path):
    args = _make_args(tmp_path, "A=changed\n", {"A": "original"})
    assert args.func(args) == 0


def test_baseline_exits_one_with_fail_on_drift(tmp_path):
    args = _make_args(tmp_path, "A=changed\n", {"A": "original"}, fail_on_drift=True)
    assert args.func(args) == 1


def test_baseline_missing_env_exits_one(tmp_path):
    snap = _write_snapshot(tmp_path / "snap.json", {"A": "1"})
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_baseline_subcommands(sub)
    args = parser.parse_args(["baseline", str(tmp_path / "ghost.env"), str(snap)])
    assert args.func(args) == 1


def test_baseline_json_format_produces_output(tmp_path, capsys):
    args = _make_args(tmp_path, "A=1\n", {"A": "1"}, fmt="json")
    args.func(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "missing_in_left" in data or "diffs" in data or isinstance(data, dict)


def test_baseline_keys_only_flag_parsed(tmp_path):
    args = _make_args(tmp_path, "A=1\n", {"A": "1"}, keys_only=True)
    assert args.keys_only is True
