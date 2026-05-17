"""CLI sub-commands for the splitter feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.differ import diff_files
from envdiff.splitter import SplitError, split_result


def add_splitter_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *split* sub-command onto *subparsers*."""
    p = subparsers.add_parser(
        "split",
        help="Split diff output into prefix-based buckets.",
    )
    p.add_argument("left", help="Base .env file.")
    p.add_argument("right", help="Target .env file.")
    p.add_argument(
        "--prefix",
        dest="prefixes",
        metavar="PREFIX",
        action="append",
        default=[],
        required=True,
        help="Prefix bucket (repeatable).  E.g. --prefix DB --prefix AWS",
    )
    p.add_argument(
        "--separator",
        default="_",
        help="Character that follows a plain prefix (default: '_').",
    )
    p.add_argument(
        "--glob",
        action="store_true",
        help="Treat each --prefix as a fnmatch glob pattern.",
    )
    p.add_argument(
        "--show-remainder",
        action="store_true",
        help="Also print keys that matched no bucket.",
    )
    p.set_defaults(func=_cmd_split)


def _cmd_split(args: argparse.Namespace) -> int:
    """Execute the *split* command and return an exit code."""
    try:
        compare = diff_files(args.left, args.right)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = split_result(
            compare,
            args.prefixes,
            separator=args.separator,
            use_glob=args.glob,
        )
    except SplitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_result(result, show_remainder=args.show_remainder)
    return 0


def _print_result(result, *, show_remainder: bool) -> None:
    for name, bucket in result.buckets.items():
        print(f"[{name}]  {len(bucket)} diff(s)")
        for diff in bucket.diffs:
            print(f"  {diff}")

    if show_remainder:
        print(f"[remainder]  {len(result.remainder)} diff(s)")
        for diff in result.remainder.diffs:
            print(f"  {diff}")
