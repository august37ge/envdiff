"""Group diff keys by prefix (e.g. DB_, AWS_, APP_) for structured reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.comparator import CompareResult, KeyDiff


class GroupError(Exception):
    """Raised when grouping fails."""


@dataclass
class KeyGroup:
    """A named collection of KeyDiff entries sharing a common prefix."""

    prefix: str
    diffs: List[KeyDiff] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.diffs)

    def __str__(self) -> str:
        return f"KeyGroup(prefix={self.prefix!r}, count={len(self.diffs)})"


@dataclass
class GroupResult:
    """Outcome of grouping a CompareResult."""

    groups: Dict[str, KeyGroup] = field(default_factory=dict)
    ungrouped: List[KeyDiff] = field(default_factory=list)

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def total_diffs(self) -> int:
        total = sum(len(g) for g in self.groups.values())
        return total + len(self.ungrouped)


def group_by_prefix(
    result: CompareResult,
    prefixes: Optional[List[str]] = None,
    separator: str = "_",
    min_prefix_length: int = 2,
) -> GroupResult:
    """Group all diffs in *result* by key prefix.

    If *prefixes* is provided only those explicit prefixes are used;
    otherwise prefixes are inferred from the keys themselves (the part
    before the first *separator*).

    Args:
        result: The CompareResult whose diffs should be grouped.
        prefixes: Optional explicit list of prefix strings (without separator).
        separator: Character that separates prefix from the rest of the key.
        min_prefix_length: Minimum length a derived prefix must have to count.

    Returns:
        A GroupResult with populated groups and any leftover ungrouped diffs.
    """
    if result is None:
        raise GroupError("result must not be None")

    all_diffs: List[KeyDiff] = (
        [KeyDiff(k, None, None) for k in result.missing_in_right]
        + [KeyDiff(k, None, None) for k in result.missing_in_left]
        + list(result.mismatches.values())
    )

    # Build the lookup set of prefixes to use
    if prefixes is not None:
        active_prefixes = [p.rstrip(separator) for p in prefixes]
    else:
        active_prefixes = _infer_prefixes(all_diffs, separator, min_prefix_length)

    group_result = GroupResult()
    for prefix in active_prefixes:
        group_result.groups[prefix] = KeyGroup(prefix=prefix)

    for diff in all_diffs:
        matched = False
        for prefix in active_prefixes:
            if diff.key.startswith(prefix + separator) or diff.key == prefix:
                group_result.groups[prefix].diffs.append(diff)
                matched = True
                break
        if not matched:
            group_result.ungrouped.append(diff)

    return group_result


def _infer_prefixes(
    diffs: List[KeyDiff],
    separator: str,
    min_length: int,
) -> List[str]:
    seen: Dict[str, int] = {}
    for diff in diffs:
        if separator in diff.key:
            prefix = diff.key.split(separator, 1)[0]
            if len(prefix) >= min_length:
                seen[prefix] = seen.get(prefix, 0) + 1
    return sorted(seen.keys())
