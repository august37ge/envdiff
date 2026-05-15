"""CLI sub-commands for multi-file diffing."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.differ_multi import MultiDiffError, diff_multi
from envdiff.formatter import format_result


def add_multi_diff_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "multi-diff",
        help="Compare multiple .env files against a single baseline.",
    )
    p.add_argument("baseline", help="Baseline .env file (reference).")
    p.add_argument("targets", nargs="+", help="Target .env files to compare.")
    p.add_argument(
        "--keys-only",
        action="store_true",
        default=False,
        help="Ignore value mismatches; report missing keys only.",
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
        help="Exit with code 1 if any diffs are found.",
    )
    p.set_defaults(func=_cmd_multi_diff)


def _cmd_multi_diff(args: argparse.Namespace) -> None:
    try:
        result = diff_multi(args.baseline, args.targets, keys_only=args.keys_only)
    except MultiDiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

    for target, cmp in result.results.items():
        print(f"--- {args.baseline}  vs  {target} ---")
        print(format_result(cmp, fmt=args.fmt))
        print()

    if args.fail_on_diff and result.any_diffs():
        sys.exit(1)
