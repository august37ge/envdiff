"""Formatting helpers for envdiff comparison results."""

import json
from typing import Any, Dict
from envdiff.comparator import CompareResult


def format_result(result: CompareResult, fmt: str = "text", show_values: bool = False) -> str:
    """Return a formatted string representation of a CompareResult.

    Args:
        result: The comparison result to format.
        fmt: Output format — ``"text"`` or ``"json"``.
        show_values: When True, include left/right values in text output.
    """
    if fmt == "json":
        return _format_json(result)
    return _format_text(result, show_values=show_values)


def _format_text(result: CompareResult, show_values: bool = False) -> str:
    lines = []
    lines.append(f"envdiff: {result.left_file}  vs  {result.right_file}")
    lines.append("-" * 50)

    if not result.has_diffs():
        lines.append("No differences found.")
        return "\n".join(lines)

    if result.missing_in_right:
        lines.append(f"\nMissing in right ({result.right_file}):")
        for key in sorted(result.missing_in_right):
            lines.append(f"  - {key}")

    if result.missing_in_left:
        lines.append(f"\nMissing in left ({result.left_file}):")
        for key in sorted(result.missing_in_left):
            lines.append(f"  - {key}")

    if result.value_mismatches:
        lines.append("\nValue mismatches:")
        for diff in sorted(result.value_mismatches, key=lambda d: d.key):
            if show_values:
                lines.append(
                    f"  ~ {diff.key}  "
                    f"[left={diff.left_value!r}  right={diff.right_value!r}]"
                )
            else:
                lines.append(f"  ~ {diff.key}")

    lines.append("")
    lines.append(_format_summary(result))
    return "\n".join(lines)


def _format_summary(result: CompareResult) -> str:
    total = (
        len(result.missing_in_left)
        + len(result.missing_in_right)
        + len(result.value_mismatches)
    )
    return (
        f"Summary: {len(result.missing_in_right)} missing in right, "
        f"{len(result.missing_in_left)} missing in left, "
        f"{len(result.value_mismatches)} mismatched values "
        f"({total} total issues)"
    )


def _format_json(result: CompareResult) -> str:
    payload: Dict[str, Any] = {
        "left_file": result.left_file,
        "right_file": result.right_file,
        "missing_in_right": sorted(result.missing_in_right),
        "missing_in_left": sorted(result.missing_in_left),
        "value_mismatches": [
            {
                "key": d.key,
                "left_value": d.left_value,
                "right_value": d.right_value,
            }
            for d in sorted(result.value_mismatches, key=lambda d: d.key)
        ],
        "has_diffs": result.has_diffs(),
    }
    return json.dumps(payload, indent=2)
