"""Multi-file diff: compare N env files pairwise against a baseline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.comparator import CompareResult
from envdiff.differ import DiffError, diff_files


@dataclass
class MultiDiffResult:
    """Holds pairwise diff results keyed by target filename."""

    baseline: str
    results: Dict[str, CompareResult] = field(default_factory=dict)

    def any_diffs(self) -> bool:
        return any(r.has_diffs() for r in self.results.values())

    def targets_with_diffs(self) -> List[str]:
        return [name for name, r in self.results.items() if r.has_diffs()]


class MultiDiffError(Exception):
    """Raised when multi-file diffing fails."""


def diff_multi(
    baseline: str | Path,
    targets: List[str | Path],
    keys_only: bool = False,
) -> MultiDiffResult:
    """Diff each target file against *baseline*.

    Args:
        baseline: Path to the reference .env file.
        targets:  One or more paths to compare against the baseline.
        keys_only: When True pass through to the underlying diff_files call.

    Returns:
        A :class:`MultiDiffResult` aggregating all pairwise comparisons.

    Raises:
        MultiDiffError: If *targets* is empty or any path is invalid.
    """
    if not targets:
        raise MultiDiffError("At least one target file must be provided.")

    baseline_path = Path(baseline)
    if not baseline_path.is_file():
        raise MultiDiffError(f"Baseline file not found: {baseline_path}")

    result = MultiDiffResult(baseline=str(baseline_path))

    for target in targets:
        target_path = Path(target)
        try:
            cmp = diff_files(baseline_path, target_path, keys_only=keys_only)
        except DiffError as exc:
            raise MultiDiffError(str(exc)) from exc
        result.results[str(target_path)] = cmp

    return result
