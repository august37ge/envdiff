"""scorer.py — compute a numeric similarity/health score for a pair of .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envdiff.comparator import CompareResult


class ScoreError(Exception):
    """Raised when scoring cannot be performed."""


@dataclass
class ScoreResult:
    """Holds the computed score and its breakdown."""

    total_keys: int
    matched_keys: int
    missing_in_left: int
    missing_in_right: int
    mismatched_values: int
    score: float  # 0.0 – 100.0
    grade: str = field(init=False)

    def __post_init__(self) -> None:
        if self.score >= 90:
            self.grade = "A"
        elif self.score >= 75:
            self.grade = "B"
        elif self.score >= 50:
            self.grade = "C"
        else:
            self.grade = "D"

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"Score: {self.score:.1f}/100 (Grade {self.grade}) "
            f"| total={self.total_keys} matched={self.matched_keys} "
            f"missing_left={self.missing_in_left} "
            f"missing_right={self.missing_in_right} "
            f"mismatched={self.mismatched_values}"
        )


def score_result(
    result: CompareResult,
    *,
    weight_missing: float = 1.0,
    weight_mismatch: float = 0.5,
) -> ScoreResult:
    """Return a :class:`ScoreResult` derived from *result*.

    Penalty per issue is weighted so that missing keys hurt more than
    value mismatches (configurable via *weight_missing* / *weight_mismatch*).
    """
    if weight_missing < 0 or weight_mismatch < 0:
        raise ScoreError("Weights must be non-negative.")

    ml = len(result.missing_in_left)
    mr = len(result.missing_in_right)
    mm = len(result.value_mismatches)

    all_keys: set[str] = set()
    # Reconstruct the full key universe from the diff data.
    for diff in result.missing_in_left:
        all_keys.add(diff.key)
    for diff in result.missing_in_right:
        all_keys.add(diff.key)
    for diff in result.value_mismatches:
        all_keys.add(diff.key)
    # Keys that are perfectly matched aren't stored in diffs; derive count.
    total = result.total_keys if hasattr(result, "total_keys") else len(all_keys) + result.matched_count  # type: ignore[attr-defined]
    # Fallback: use the union size as a lower-bound total.
    if total == 0:
        total = ml + mr + mm

    matched = max(0, total - ml - mr - mm)

    if total == 0:
        raw_score = 100.0
    else:
        penalty = (ml + mr) * weight_missing + mm * weight_mismatch
        max_penalty = total * max(weight_missing, weight_mismatch)
        raw_score = max(0.0, 100.0 * (1.0 - penalty / max_penalty)) if max_penalty else 100.0

    return ScoreResult(
        total_keys=total,
        matched_keys=matched,
        missing_in_left=ml,
        missing_in_right=mr,
        mismatched_values=mm,
        score=round(raw_score, 2),
    )
