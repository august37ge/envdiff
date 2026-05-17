"""CLI sub-commands for differ_stats: compute aggregate diff statistics."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ import diff_files
from envdiff.differ_stats import StatsError, compute_stats


def add_stats_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "stats",
        help="Compute aggregate diff statistics across multiple file pairs.",
    )
    p.add_argument(
        "pairs",
        nargs="+",
        metavar="LEFT:RIGHT",
        help="Colon-separated file pairs to compare, e.g. .env.dev:.env.prod",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-diffs",
        action="store_true",
        default=False,
        help="Exit with code 1 if any diffs are found.",
    )
    p.set_defaults(func=_cmd_stats)


def _cmd_stats(args: argparse.Namespace) -> int:
    results = []
    errors: List[str] = []

    for pair in args.pairs:
        if ":" not in pair:
            errors.append(f"Invalid pair (expected LEFT:RIGHT): {pair!r}")
            continue
        left, right = pair.split(":", 1)
        try:
            results.append(diff_files(left, right))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{pair}: {exc}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    try:
        stats = compute_stats(results)
    except StatsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "json":
        print(
            json.dumps(
                {
                    "file_count": stats.file_count,
                    "total_keys": stats.total_keys,
                    "total_ok": stats.total_ok,
                    "total_diffs": stats.total_diffs,
                    "total_missing_left": stats.total_missing_left,
                    "total_missing_right": stats.total_missing_right,
                    "total_mismatches": stats.total_mismatches,
                    "health_pct": stats.health_pct,
                },
                indent=2,
            )
        )
    else:
        print(stats)

    return 1 if (args.fail_on_diffs and stats.total_diffs > 0) else 0
