"""CLI sub-commands for filtering compare results."""

from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff_files
from envdiff.filterer import FilterOptions, filter_result, FilterError
from envdiff.reporter import ReportOptions, generate_report


def add_filterer_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "filter",
        help="Compare two .env files and filter the diff output.",
    )
    p.add_argument("left", help="Left / base .env file.")
    p.add_argument("right", help="Right / target .env file.")
    p.add_argument("--pattern", default=None, help="Glob (or regex) pattern to include keys.")
    p.add_argument("--exclude", default=None, dest="exclude_pattern", help="Glob (or regex) pattern to exclude keys.")
    p.add_argument("--regex", action="store_true", help="Treat --pattern / --exclude as regular expressions.")
    p.add_argument("--missing-only", action="store_true", help="Show only keys missing in either file.")
    p.add_argument("--mismatch-only", action="store_true", help="Show only keys with differing values.")
    p.add_argument("--format", choices=["text", "json", "summary"], default="text", dest="fmt")
    p.set_defaults(func=_cmd_filter)


def _cmd_filter(args: argparse.Namespace) -> int:
    try:
        result = diff_files(args.left, args.right)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    options = FilterOptions(
        pattern=args.pattern,
        use_regex=args.regex,
        missing_only=args.missing_only,
        mismatch_only=args.mismatch_only,
        exclude_pattern=args.exclude_pattern,
    )

    try:
        filtered = filter_result(result, options)
    except FilterError as exc:
        print(f"filter error: {exc}", file=sys.stderr)
        return 1

    report_opts = ReportOptions(format=args.fmt)
    print(generate_report(filtered, report_opts))
    return 0 if not filtered.has_diffs() else 1
