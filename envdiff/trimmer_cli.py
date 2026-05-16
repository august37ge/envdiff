"""trimmer_cli.py – CLI sub-commands for the trimmer feature."""
from __future__ import annotations

import argparse
import sys

from envdiff.trimmer import TrimError, trim_file, write_trimmed


def add_trimmer_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "trim",
        help="Strip leading/trailing whitespace from .env values.",
    )
    p.add_argument("file", help="Path to the .env file to trim.")
    p.add_argument(
        "-o", "--output",
        metavar="OUTPUT",
        help="Write trimmed file to OUTPUT instead of stdout.",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if any values would be trimmed (dry-run).",
    )
    p.set_defaults(func=_cmd_trim)


def _cmd_trim(args: argparse.Namespace) -> int:
    try:
        result = trim_file(args.file)
    except TrimError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if result.has_changes:
            for entry in result.changed_entries:
                print(f"  {entry}")
            print(
                f"\n{len(result.changed_entries)} value(s) have surrounding whitespace.",
                file=sys.stderr,
            )
            return 1
        print("All values are already trimmed.")
        return 0

    if args.output:
        write_trimmed(result, args.output)
        print(f"Trimmed file written to {args.output}")
    else:
        for entry in result.entries:
            print(f"{entry.key}={entry.trimmed}")

    return 0
