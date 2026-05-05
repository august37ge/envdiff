"""Command-line interface for envdiff."""

import sys
import argparse
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare_envs
from envdiff.formatter import format_result, OutputFormat


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files and surface missing or mismatched keys.",
    )
    p.add_argument("left", type=Path, help="Base .env file")
    p.add_argument("right", type=Path, help="Target .env file to compare against")
    p.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "summary"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--keys-only",
        action="store_true",
        help="Only check for missing keys; ignore value differences",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if differences are found",
    )
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        left_env = parse_env_file(args.left)
    except (EnvParseError, OSError) as exc:
        print(f"envdiff: error reading {args.left}: {exc}", file=sys.stderr)
        return 2

    try:
        right_env = parse_env_file(args.right)
    except (EnvParseError, OSError) as exc:
        print(f"envdiff: error reading {args.right}: {exc}", file=sys.stderr)
        return 2

    result = compare_envs(
        left_env,
        right_env,
        left_path=str(args.left),
        right_path=str(args.right),
        keys_only=args.keys_only,
    )

    print(format_result(result, fmt=args.fmt))

    if args.exit_code and result.has_diffs:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
