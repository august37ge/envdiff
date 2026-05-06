"""CLI helpers for snapshot sub-commands: ``save`` and ``diff-snapshot``."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace

from envdiff.comparator import compare
from envdiff.formatter import format_result
from envdiff.parser import parse_env_file, EnvParseError
from envdiff.snapshot import SnapshotError, load_snapshot, save_snapshot


def add_snapshot_subcommands(subparsers) -> None:  # type: ignore[type-arg]
    """Register snapshot-related sub-commands onto an existing subparsers object."""
    # save-snapshot
    sp_save = subparsers.add_parser(
        "save-snapshot",
        help="Compare two .env files and save the result as a JSON snapshot.",
    )
    sp_save.add_argument("left", help="Left .env file")
    sp_save.add_argument("right", help="Right .env file")
    sp_save.add_argument("-o", "--output", required=True, help="Output snapshot path")
    sp_save.set_defaults(func=_cmd_save_snapshot)

    # load-snapshot
    sp_load = subparsers.add_parser(
        "load-snapshot",
        help="Display a previously saved snapshot.",
    )
    sp_load.add_argument("snapshot", help="Path to snapshot JSON file")
    sp_load.add_argument(
        "--format",
        choices=["text", "json", "summary"],
        default="text",
        dest="fmt",
    )
    sp_load.set_defaults(func=_cmd_load_snapshot)


def _cmd_save_snapshot(args: Namespace) -> int:
    try:
        left_env = parse_env_file(args.left)
        right_env = parse_env_file(args.right)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    result = compare(left_env, right_env)
    try:
        save_snapshot(result, args.output, left_name=args.left, right_name=args.right)
    except SnapshotError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Snapshot saved to {args.output}")
    return 0


def _cmd_load_snapshot(args: Namespace) -> int:
    try:
        result, meta = load_snapshot(args.snapshot)
    except SnapshotError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        f"Snapshot from {meta.get('created_at', 'unknown')}  "
        f"[{meta.get('left')} vs {meta.get('right')}]"
    )
    output = format_result(result, fmt=args.fmt)
    print(output)
    return 0 if not result.has_diffs() else 1
