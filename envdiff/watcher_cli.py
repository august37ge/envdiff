"""CLI subcommands for the envdiff watcher feature."""

import argparse
import sys

from envdiff.watcher import watch, WatchError
from envdiff.formatter import format_result


def add_watcher_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'watch' subcommand onto *subparsers*."""
    p = subparsers.add_parser(
        "watch",
        help="Watch two .env files and print diffs whenever they change.",
    )
    p.add_argument("left", help="Path to the left/base .env file.")
    p.add_argument("right", help="Path to the right .env file.")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0).",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "summary", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=_cmd_watch)


def _cmd_watch(args: argparse.Namespace) -> int:
    """Handler for the 'watch' subcommand."""

    def _on_change(result):
        output = format_result(result, fmt=args.fmt)
        print(output, flush=True)

    try:
        print(
            f"Watching {args.left!r} vs {args.right!r} every {args.interval}s "
            "— press Ctrl+C to stop.",
            flush=True,
        )
        watch(args.left, args.right, on_change=_on_change, interval=args.interval)
    except WatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nWatcher stopped.", flush=True)

    return 0
