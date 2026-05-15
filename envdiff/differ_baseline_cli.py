"""CLI sub-commands for baseline comparison."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ_baseline import BaselineError, diff_against_baseline
from envdiff.formatter import format_result


def add_baseline_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "baseline",
        help="Compare a .env file against a saved snapshot baseline",
    )
    p.add_argument("env", help="Path to the live .env file")
    p.add_argument("baseline", help="Path to the saved snapshot (.json)")
    p.add_argument(
        "--keys-only",
        action="store_true",
        default=False,
        help="Ignore value differences; report missing keys only",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "summary"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-drift",
        action="store_true",
        default=False,
        help="Exit with code 1 when drift is detected",
    )
    p.set_defaults(func=_cmd_baseline)


def _cmd_baseline(args: argparse.Namespace) -> int:
    try:
        result = diff_against_baseline(
            env_path=args.env,
            baseline_path=args.baseline,
            keys_only=args.keys_only,
        )
    except BaselineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(format_result(result.compare, fmt=args.fmt))

    if args.fail_on_drift and result.has_diffs:
        return 1
    return 0
