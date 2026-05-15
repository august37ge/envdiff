"""CLI subcommands for the ranker feature."""
from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff_files
from envdiff.ranker import RankError, Severity, rank_result


def add_ranker_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "rank",
        help="Rank keys by diff severity (missing > mismatch > ok)",
    )
    p.add_argument("left", help="Left .env file")
    p.add_argument("right", help="Right .env file")
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show only the top N highest-severity keys (0 = all)",
    )
    p.add_argument(
        "--min-severity",
        choices=["ok", "mismatch", "missing"],
        default="ok",
        help="Filter to keys at or above this severity level",
    )
    p.set_defaults(func=_cmd_rank)


def _cmd_rank(args: argparse.Namespace) -> int:
    try:
        compare_result = diff_files(args.left, args.right)
        rank = rank_result(compare_result)
    except RankError as exc:
        print(f"rank error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    min_sev = Severity[args.min_severity.upper()]
    entries = [
        r for r in rank.by_severity() if r.severity >= min_sev
    ]

    if args.top > 0:
        entries = entries[: args.top]

    if not entries:
        print("No keys match the given criteria.")
        return 0

    print(f"{'SEVERITY':<12} {'KEY':<40} LEFT VALUE          RIGHT VALUE")
    print("-" * 80)
    for r in entries:
        lv = r.left_value if r.left_value is not None else "<absent>"
        rv = r.right_value if r.right_value is not None else "<absent>"
        print(f"{r.severity.name:<12} {r.key:<40} {lv:<20} {rv}")

    return 0
