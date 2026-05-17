"""Compute statistical summary of diff results across multiple comparisons."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.comparator import CompareResult


class StatsError(Exception):
    """Raised when stats computation fails."""


@dataclass
class DiffStats:
    """Aggregated statistics over one or more CompareResult objects."""

    total_keys: int = 0
    total_missing_left: int = 0
    total_missing_right: int = 0
    total_mismatches: int = 0
    total_ok: int = 0
    file_count: int = 0

    @property
    def total_diffs(self) -> int:
        return self.total_missing_left + self.total_missing_right + self.total_mismatches

    @property
    def health_pct(self) -> float:
        """Percentage of keys that are identical (0-100)."""
        if self.total_keys == 0:
            return 100.0
        return round(self.total_ok / self.total_keys * 100, 2)

    def __str__(self) -> str:
        return (
            f"Files: {self.file_count} | Keys: {self.total_keys} | "
            f"OK: {self.total_ok} | Diffs: {self.total_diffs} "
            f"(missing_left={self.total_missing_left}, "
            f"missing_right={self.total_missing_right}, "
            f"mismatch={self.total_mismatches}) | "
            f"Health: {self.health_pct}%"
        )


def compute_stats(results: List[Optional[CompareResult]]) -> DiffStats:
    """Aggregate statistics from a list of CompareResult objects.

    Args:
        results: List of CompareResult instances (None entries are skipped).

    Returns:
        DiffStats with aggregated counts.

    Raises:
        StatsError: If results is empty or all entries are None.
    """
    if not results:
        raise StatsError("No results provided to compute_stats.")

    valid = [r for r in results if r is not None]
    if not valid:
        raise StatsError("All results are None; nothing to aggregate.")

    stats = DiffStats(file_count=len(valid))

    for result in valid:
        ml = len(result.missing_in_left)
        mr = len(result.missing_in_right)
        mm = len(result.mismatches)
        all_keys = set(result.missing_in_left) | set(result.missing_in_right) | {d.key for d in result.mismatches}
        # ok keys: present in both with same value — derive from diffs vs total
        # We reconstruct total unique keys touched by this result
        ok = max(0, len(all_keys) - ml - mr - mm)
        stats.total_missing_left += ml
        stats.total_missing_right += mr
        stats.total_mismatches += mm
        stats.total_ok += ok
        stats.total_keys += ml + mr + mm + ok

    return stats
