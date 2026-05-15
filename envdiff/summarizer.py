"""Summarizer: produce a human-readable health summary from a CompareResult."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envdiff.comparator import CompareResult
from envdiff.scorer import score_result, ScoreResult


class SummaryError(Exception):
    """Raised when summary generation fails."""


@dataclass
class SummaryReport:
    total_keys: int
    missing_in_left: int
    missing_in_right: int
    mismatches: int
    score: ScoreResult
    health: str  # "healthy" | "warning" | "critical"

    def __str__(self) -> str:
        lines = [
            f"Health  : {self.health.upper()}",
            f"Score   : {self.score.score:.1f} / 100",
            f"Total   : {self.total_keys} unique key(s)",
            f"Missing in left  : {self.missing_in_left}",
            f"Missing in right : {self.missing_in_right}",
            f"Mismatches       : {self.mismatches}",
        ]
        return "\n".join(lines)


def _health_label(score: float) -> str:
    if score >= 90.0:
        return "healthy"
    if score >= 60.0:
        return "warning"
    return "critical"


def summarize(result: CompareResult) -> SummaryReport:
    """Build a SummaryReport from a CompareResult."""
    if result is None:
        raise SummaryError("result must not be None")

    score = score_result(result)

    all_keys: set[str] = set()
    for diff in result.diffs:
        all_keys.add(diff.key)

    return SummaryReport(
        total_keys=len(all_keys),
        missing_in_left=len(result.missing_in_left()),
        missing_in_right=len(result.missing_in_right()),
        mismatches=len(result.value_mismatches()),
        score=score,
        health=_health_label(score.score),
    )


def format_summary(report: SummaryReport, fmt: str = "text") -> str:
    """Render a SummaryReport as text or JSON."""
    if fmt == "json":
        import json
        return json.dumps({
            "health": report.health,
            "score": round(report.score.score, 2),
            "total_keys": report.total_keys,
            "missing_in_left": report.missing_in_left,
            "missing_in_right": report.missing_in_right,
            "mismatches": report.mismatches,
        }, indent=2)
    if fmt == "text":
        return str(report)
    raise SummaryError(f"Unknown format: {fmt!r}. Choose 'text' or 'json'.")
