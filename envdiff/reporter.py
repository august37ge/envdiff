"""Report generation for envdiff comparison results."""

from dataclasses import dataclass, field
from typing import Optional
from envdiff.comparator import CompareResult
from envdiff.formatter import format_result


@dataclass
class ReportOptions:
    """Options controlling report output."""
    format: str = "text"  # "text" or "json"
    show_values: bool = False
    summary_only: bool = False
    output_file: Optional[str] = None


def generate_report(result: CompareResult, options: ReportOptions) -> str:
    """Generate a formatted report string from a comparison result."""
    if options.summary_only:
        lines = []
        total = (
            len(result.missing_in_left)
            + len(result.missing_in_right)
            + len(result.value_mismatches)
        )
        lines.append(f"Missing in left:  {len(result.missing_in_left)}")
        lines.append(f"Missing in right: {len(result.missing_in_right)}")
        lines.append(f"Value mismatches: {len(result.value_mismatches)}")
        lines.append(f"Total issues:     {total}")
        return "\n".join(lines)

    return format_result(result, fmt=options.format, show_values=options.show_values)


def write_report(result: CompareResult, options: ReportOptions) -> None:
    """Generate a report and write it to a file or stdout."""
    import sys

    content = generate_report(result, options)

    if options.output_file:
        with open(options.output_file, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.write("\n")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")
