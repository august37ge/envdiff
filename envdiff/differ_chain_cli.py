"""CLI sub-commands for chained .env diff."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ_chain import ChainError, diff_chain
from envdiff.formatter import format_result


def add_chain_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "chain",
        help="Compare consecutive pairs of .env files along a chain.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare in order.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "summary"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 when any differences are found.",
    )
    p.set_defaults(func=_cmd_chain)


def _cmd_chain(args: argparse.Namespace) -> int:
    try:
        chain = diff_chain(args.files)
    except ChainError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for link in chain.links:
        header = f"=== {Path(link.left).name} -> {Path(link.right).name} ==="
        print(header)
        print(format_result(link.result, fmt=args.fmt))

    if args.fail_on_diff and chain.any_diffs():
        return 1
    return 0
