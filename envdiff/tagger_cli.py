"""CLI sub-commands for the tagger module."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.differ import diff_files
from envdiff.tagger import TagError, TagRule, tag_result


def add_tagger_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tag", help="Tag differing keys with labels")
    p.add_argument("left", help="Left .env file")
    p.add_argument("right", help="Right .env file")
    p.add_argument(
        "--rule",
        dest="rules",
        metavar="PATTERN:TAG",
        action="append",
        default=[],
        help="Tagging rule as PATTERN:TAG (repeatable, glob patterns supported)",
    )
    p.add_argument(
        "--untagged",
        action="store_true",
        help="Show only untagged keys",
    )
    p.set_defaults(func=_cmd_tag)


def _cmd_tag(args: argparse.Namespace) -> int:
    rules: List[TagRule] = []
    for raw in args.rules:
        if ":" not in raw:
            print(f"error: rule '{raw}' must be in PATTERN:TAG format", file=sys.stderr)
            return 2
        pattern, _, tag = raw.partition(":")
        rules.append(TagRule(pattern=pattern.strip(), tag=tag.strip()))

    try:
        result = diff_files(args.left, args.right)
        tag_res = tag_result(result, rules)
    except TagError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    keys_to_show = tag_res.untagged() if args.untagged else tag_res.tagged

    if not keys_to_show:
        print("No keys to display.")
        return 0

    for tk in keys_to_show:
        print(str(tk))

    return 0
