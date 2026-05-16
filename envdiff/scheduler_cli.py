"""scheduler_cli.py – CLI subcommands for the scheduler feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_files
from envdiff.scheduler import SchedulerError, ScheduleLog, load_log, record_run, save_log


def add_scheduler_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register *schedule-run* and *schedule-log* subcommands."""
    run_p = subparsers.add_parser(
        "schedule-run",
        help="Run a diff and append the result to a schedule log.",
    )
    run_p.add_argument("left", help="Base .env file.")
    run_p.add_argument("right", help="Target .env file.")
    run_p.add_argument(
        "--log",
        default="envdiff_schedule.json",
        help="Path to the schedule log file (default: envdiff_schedule.json).",
    )
    run_p.add_argument(
        "--fail-on-diffs",
        action="store_true",
        help="Exit with code 1 when diffs are found.",
    )
    run_p.set_defaults(func=_cmd_schedule_run)

    log_p = subparsers.add_parser(
        "schedule-log",
        help="Display entries from a schedule log.",
    )
    log_p.add_argument(
        "--log",
        default="envdiff_schedule.json",
        help="Path to the schedule log file.",
    )
    log_p.add_argument(
        "--last",
        type=int,
        default=0,
        help="Show only the last N entries (0 = all).",
    )
    log_p.set_defaults(func=_cmd_schedule_log)


def _cmd_schedule_run(args: argparse.Namespace) -> int:
    try:
        result = diff_files(args.left, args.right)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    entry = record_run(args.left, args.right, result)
    log = ScheduleLog(entries=[entry])
    try:
        save_log(log, Path(args.log))
    except SchedulerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    status = "DIFFS" if entry.has_diffs else "OK"
    print(
        f"[{status}] left={args.left} right={args.right} "
        f"missing_left={entry.missing_in_left} "
        f"missing_right={entry.missing_in_right} "
        f"mismatches={entry.mismatches}"
    )
    return 1 if (args.fail_on_diffs and entry.has_diffs) else 0


def _cmd_schedule_log(args: argparse.Namespace) -> int:
    try:
        log = load_log(Path(args.log))
    except SchedulerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    entries = log.entries
    if args.last > 0:
        entries = entries[-args.last :]

    if not entries:
        print("No entries found.")
        return 0

    for e in entries:
        import datetime

        ts = datetime.datetime.fromtimestamp(e.timestamp).isoformat()
        status = "DIFFS" if e.has_diffs else "OK"
        print(f"{ts}  [{status}]  {e.left} vs {e.right}  ml={e.missing_in_left} mr={e.missing_in_right} mm={e.mismatches}")
    return 0
