"""Tests for envdiff.differ_stats_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.differ_stats_cli import add_stats_subcommands


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _make_args(pairs, fmt="text", fail_on_diffs=False):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_stats_subcommands(sub)
    argv = ["stats"] + pairs
    if fmt != "text":
        argv += ["--format", fmt]
    if fail_on_diffs:
        argv.append("--fail-on-diffs")
    return parser.parse_args(argv)


def test_stats_exits_zero_identical(tmp_path):
    left = _write(tmp_path, "left.env", "KEY=value\n")
    right = _write(tmp_path, "right.env", "KEY=value\n")
    args = _make_args([f"{left}:{right}"])
    assert args.func(args) == 0


def test_stats_exits_zero_with_diffs_no_fail_flag(tmp_path):
    left = _write(tmp_path, "left.env", "KEY=value\n")
    right = _write(tmp_path, "right.env", "OTHER=value\n")
    args = _make_args([f"{left}:{right}"])
    assert args.func(args) == 0


def test_stats_exits_one_with_diffs_and_fail_flag(tmp_path):
    left = _write(tmp_path, "left.env", "KEY=value\n")
    right = _write(tmp_path, "right.env", "OTHER=value\n")
    args = _make_args([f"{left}:{right}"], fail_on_diffs=True)
    assert args.func(args) == 1


def test_stats_json_output(tmp_path, capsys):
    left = _write(tmp_path, "left.env", "KEY=value\n")
    right = _write(tmp_path, "right.env", "KEY=value\n")
    args = _make_args([f"{left}:{right}"], fmt="json")
    args.func(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "health_pct" in data
    assert data["file_count"] == 1


def test_invalid_pair_returns_error(tmp_path, capsys):
    args = _make_args(["not-a-valid-pair"])
    rc = args.func(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "ERROR" in captured.err


def test_missing_file_returns_error(tmp_path, capsys):
    args = _make_args([f"{tmp_path}/ghost.env:{tmp_path}/also_ghost.env"])
    rc = args.func(args)
    assert rc == 1
