"""Export CompareResult to various file formats (CSV, Markdown)."""

from __future__ import annotations

import csv
import io
from typing import Literal

from envdiff.comparator import CompareResult

ExportFormat = Literal["csv", "markdown"]


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_result(result: CompareResult, fmt: ExportFormat) -> str:
    """Return *result* serialised as *fmt* (csv or markdown)."""
    if fmt == "csv":
        return _export_csv(result)
    if fmt == "markdown":
        return _export_markdown(result)
    raise ExportError(f"Unsupported export format: {fmt!r}")


def write_export(result: CompareResult, fmt: ExportFormat, path: str) -> None:
    """Write the exported content to *path*."""
    content = export_result(result, fmt)
    try:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
    except OSError as exc:
        raise ExportError(f"Cannot write export file {path!r}: {exc}") from exc


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _export_csv(result: CompareResult) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["key", "status", "left_value", "right_value"])
    for key in sorted(result.missing_in_right):
        writer.writerow([key, "missing_in_right", result.left.get(key, ""), ""])
    for key in sorted(result.missing_in_left):
        writer.writerow([key, "missing_in_left", "", result.right.get(key, "")])
    for diff in sorted(result.value_diffs, key=lambda d: d.key):
        writer.writerow([diff.key, "value_mismatch", diff.left_value, diff.right_value])
    return buf.getvalue()


def _export_markdown(result: CompareResult) -> str:
    lines: list[str] = []
    lines.append("# envdiff Report")
    lines.append("")
    if not result.has_diffs():
        lines.append("_No differences found._")
        return "\n".join(lines)

    lines.append("| Key | Status | Left Value | Right Value |")
    lines.append("|-----|--------|------------|-------------|")
    for key in sorted(result.missing_in_right):
        lines.append(f"| `{key}` | missing in right | `{result.left.get(key, '')}` | — |")
    for key in sorted(result.missing_in_left):
        lines.append(f"| `{key}` | missing in left | — | `{result.right.get(key, '')}` |")
    for diff in sorted(result.value_diffs, key=lambda d: d.key):
        lines.append(
            f"| `{diff.key}` | value mismatch | `{diff.left_value}` | `{diff.right_value}` |"
        )
    return "\n".join(lines)
