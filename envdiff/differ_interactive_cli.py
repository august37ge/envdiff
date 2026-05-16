"""CLI subcommand: interactive side-by-side diff."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.differ_interactive import InteractiveDiffError, SideBySideResult, diff_interactive


def add_interactive_diff_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "idiff",
        help="Show a side-by-side interactive diff of two .env files",
    )
    p.add_argument("left", help="Base .env file")
    p.add_argument("right", help="Target .env file")
    p.add_argument(
        "--only",
        choices=["ok", "missing_left", "missing_right", "mismatch"],
        default=None,
        help="Filter rows by status",
    )
    p.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 when any diff is found",
    )
    p.set_defaults(func=_cmd_idiff)


def _print_result(result: SideBySideResult, only: str | None) -> None:
    header = f"{'KEY':<30}  {'LEFT':<25}  {'RIGHT':<25}  STATUS"
    separator = "-" * len(header)
    print(header)
    print(separator)

    rows = result.rows_with_status(only) if only else result.rows
    if not rows:
        print("(no rows to display)")
        return
    for row in rows:
        print(str(row))

    print(separator)
    totals = {"ok": 0, "missing_left": 0, "missing_right": 0, "mismatch": 0}
    for row in result.rows:
        totals[row.status] = totals.get(row.status, 0) + 1
    print(
        f"ok={totals['ok']}  missing_left={totals['missing_left']}  "
        f"missing_right={totals['missing_right']}  mismatch={totals['mismatch']}"
    )


def _cmd_idiff(args: argparse.Namespace) -> int:
    try:
        result = diff_interactive(args.left, args.right)
    except InteractiveDiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_result(result, getattr(args, "only", None))

    if args.fail_on_diff and result.has_diffs:
        return 1
    return 0
