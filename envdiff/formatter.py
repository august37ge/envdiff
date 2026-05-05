"""Output formatters for CompareResult."""

import json
from typing import Literal

from envdiff.comparator import CompareResult

OutputFormat = Literal["text", "json", "summary"]


def format_result(result: CompareResult, fmt: OutputFormat = "text") -> str:
    """Render a CompareResult as a string in the requested format."""
    if fmt == "json":
        return _format_json(result)
    elif fmt == "summary":
        return _format_summary(result)
    return _format_text(result)


def _format_text(result: CompareResult) -> str:
    lines = [
        f"Comparing: {result.left_path}  vs  {result.right_path}",
        "-" * 60,
    ]
    if not result.has_diffs:
        lines.append("No differences found.")
        return "\n".join(lines)

    if result.missing_in_left:
        lines.append(f"Missing in {result.left_path} ({len(result.missing_in_left)}):")
        for d in result.missing_in_left:
            lines.append(str(d))

    if result.missing_in_right:
        lines.append(f"Missing in {result.right_path} ({len(result.missing_in_right)}):")
        for d in result.missing_in_right:
            lines.append(str(d))

    if result.mismatched:
        lines.append(f"Value mismatches ({len(result.mismatched)}):")
        for d in result.mismatched:
            lines.append(str(d))

    return "\n".join(lines)


def _format_summary(result: CompareResult) -> str:
    total = len(result.diffs)
    if total == 0:
        return "OK — no differences."
    parts = []
    if result.missing_in_left:
        parts.append(f"{len(result.missing_in_left)} missing in left")
    if result.missing_in_right:
        parts.append(f"{len(result.missing_in_right)} missing in right")
    if result.mismatched:
        parts.append(f"{len(result.mismatched)} mismatched")
    return f"Found {total} difference(s): " + ", ".join(parts) + "."


def _format_json(result: CompareResult) -> str:
    payload = {
        "left": result.left_path,
        "right": result.right_path,
        "diffs": [
            {
                "key": d.key,
                "status": d.status,
                "left_value": d.left_value,
                "right_value": d.right_value,
            }
            for d in result.diffs
        ],
    }
    return json.dumps(payload, indent=2)
