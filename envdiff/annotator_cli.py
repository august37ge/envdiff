"""annotator_cli.py – CLI sub-commands for the annotator feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.annotator import AnnotatorError, annotate_result, load_annotations
from envdiff.differ import diff_files


def add_annotator_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "annotate",
        help="Show diff with annotations from an annotations file",
    )
    p.add_argument("left", help="Base .env file")
    p.add_argument("right", help="Target .env file")
    p.add_argument(
        "--annotations",
        metavar="FILE",
        required=True,
        help="Path to annotations file (KEY = \"comment\" format)",
    )
    p.add_argument(
        "--only-annotated",
        action="store_true",
        help="Only print keys that have an annotation",
    )
    p.set_defaults(func=_cmd_annotate)


def _cmd_annotate(args: argparse.Namespace) -> int:
    try:
        result = diff_files(Path(args.left), Path(args.right))
        annotations = load_annotations(Path(args.annotations))
        ar = annotate_result(result, annotations)
    except (AnnotatorError, Exception) as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if ar.total == 0:
        print("No diffs found.")
        return 0

    for ak in ar.annotated:
        if args.only_annotated and ak.annotation is None:
            continue
        print(str(ak))

    print(
        f"\n{ar.total} diff(s); {ar.unannotated_count} without annotation."
    )
    return 0
