"""Tests for envdiff.annotator_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

from envdiff.annotator_cli import _cmd_annotate, add_annotator_subcommands


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _make_args(tmp_path, left_content, right_content, ann_content, only_annotated=False):
    left = _write(tmp_path, "left.env", left_content)
    right = _write(tmp_path, "right.env", right_content)
    ann = _write(tmp_path, "ann.txt", ann_content)
    ns = argparse.Namespace(
        left=str(left),
        right=str(right),
        annotations=str(ann),
        only_annotated=only_annotated,
    )
    return ns


def test_annotate_exits_zero_no_diffs(tmp_path):
    args = _make_args(tmp_path, "KEY=val\n", "KEY=val\n", "")
    assert _cmd_annotate(args) == 0


def test_annotate_exits_zero_with_diffs(tmp_path):
    args = _make_args(
        tmp_path,
        "DB_HOST=localhost\n",
        "",
        'DB_HOST = "primary host"\n',
    )
    assert _cmd_annotate(args) == 0


def test_annotate_missing_annotation_file_returns_error(tmp_path):
    left = _write(tmp_path, "left.env", "A=1\n")
    right = _write(tmp_path, "right.env", "")
    ns = argparse.Namespace(
        left=str(left),
        right=str(right),
        annotations=str(tmp_path / "nonexistent.txt"),
        only_annotated=False,
    )
    assert _cmd_annotate(ns) == 1


def test_annotate_only_annotated_flag(tmp_path, capsys):
    args = _make_args(
        tmp_path,
        "DB_HOST=localhost\nPORT=5432\n",
        "",
        'DB_HOST = "host note"\n',
        only_annotated=True,
    )
    _cmd_annotate(args)
    captured = capsys.readouterr().out
    assert "DB_HOST" in captured
    # PORT has no annotation and should be suppressed
    assert "PORT" not in captured


def test_add_annotator_subcommands_registers_annotate(tmp_path):
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_annotator_subcommands(subs)
    args = parser.parse_args([
        "annotate",
        "left.env",
        "right.env",
        "--annotations", "ann.txt",
    ])
    assert args.left == "left.env"
    assert args.right == "right.env"
    assert args.annotations == "ann.txt"
    assert args.only_annotated is False
