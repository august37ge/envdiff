"""CLI sub-commands for the streaker feature.

Subcommands
-----------
streak show   – print the current streak for a file pair
streak record – run a diff and update the streak file
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_files
from envdiff.streaker import (
    StreakRecord,
    StreakerError,
    load_streak,
    record_run,
    save_streak,
)


def add_streaker_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    streak_p = subparsers.add_parser("streak", help="Track clean-diff streaks")
    streak_sub = streak_p.add_subparsers(dest="streak_cmd", required=True)

    # streak show
    show_p = streak_sub.add_parser("show", help="Display current streak")
    show_p.add_argument("streak_file", help="Path to streak JSON file")
    show_p.set_defaults(func=_cmd_show)

    # streak record
    rec_p = streak_sub.add_parser("record", help="Run diff and record result")
    rec_p.add_argument("left", help="Left .env file")
    rec_p.add_argument("right", help="Right .env file")
    rec_p.add_argument("streak_file", help="Path to streak JSON file (created if absent)")
    rec_p.set_defaults(func=_cmd_record)


def _cmd_show(args: argparse.Namespace) -> int:
    path = Path(args.streak_file)
    if not path.exists():
        print("No streak file found.", file=sys.stderr)
        return 1
    try:
        rec = load_streak(path)
    except StreakerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Pair : {rec.left}  ↔  {rec.right}")
    print(f"Current streak : {rec.current_streak}")
    print(f"Best streak    : {rec.best_streak}")
    clean_label = {True: "clean", False: "dirty", None: "n/a"}[rec.last_run_clean]
    print(f"Last run       : {clean_label}")
    return 0


def _cmd_record(args: argparse.Namespace) -> int:
    path = Path(args.streak_file)
    if path.exists():
        try:
            rec = load_streak(path)
        except StreakerError as exc:
            print(f"Error loading streak: {exc}", file=sys.stderr)
            return 1
    else:
        rec = StreakRecord(left=args.left, right=args.right)

    try:
        result = diff_files(args.left, args.right)
    except Exception as exc:  # noqa: BLE001
        print(f"Diff error: {exc}", file=sys.stderr)
        return 1

    is_clean = not result.has_diffs()
    record_run(rec, is_clean)

    try:
        save_streak(rec, path)
    except StreakerError as exc:
        print(f"Error saving streak: {exc}", file=sys.stderr)
        return 1

    status = "clean" if is_clean else "dirty"
    print(f"Run recorded ({status}). Current streak: {rec.current_streak}")
    return 0 if is_clean else 2
