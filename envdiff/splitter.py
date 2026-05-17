"""Split a CompareResult into per-prefix buckets for targeted analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional

from envdiff.comparator import CompareResult, KeyDiff


class SplitError(ValueError):
    """Raised when split_result is called with invalid arguments."""


@dataclass
class SplitBucket:
    """A named slice of a CompareResult containing only matching KeyDiffs."""

    name: str
    diffs: List[KeyDiff] = field(default_factory=list)

    def __len__(self) -> int:  # noqa: D105
        return len(self.diffs)

    def __str__(self) -> str:  # noqa: D105
        return f"SplitBucket({self.name!r}, {len(self.diffs)} diffs)"

    @property
    def has_diffs(self) -> bool:
        """Return True when the bucket contains at least one diff."""
        return bool(self.diffs)


@dataclass
class SplitResult:
    """Container returned by :func:`split_result`."""

    buckets: Dict[str, SplitBucket] = field(default_factory=dict)
    remainder: SplitBucket = field(default_factory=lambda: SplitBucket("__remainder__"))

    @property
    def any_diffs(self) -> bool:
        """Return True when any bucket (or remainder) contains diffs."""
        return any(b.has_diffs for b in self.buckets.values()) or self.remainder.has_diffs

    def bucket_names(self) -> List[str]:
        """Ordered list of bucket names."""
        return list(self.buckets.keys())


def split_result(
    result: Optional[CompareResult],
    prefixes: List[str],
    *,
    separator: str = "_",
    use_glob: bool = False,
) -> SplitResult:
    """Partition *result* diffs into buckets keyed by *prefixes*.

    Each diff key is matched against the supplied prefixes in order.
    The first match wins.  Unmatched diffs land in ``remainder``.

    Args:
        result: A :class:`~envdiff.comparator.CompareResult` to split.
        prefixes: Ordered list of prefix strings (or glob patterns when
            *use_glob* is ``True``).
        separator: Character appended to each prefix before plain-prefix
            matching (ignored when *use_glob* is ``True``).
        use_glob: When ``True``, treat each prefix as a :mod:`fnmatch`
            glob pattern matched against the full key.

    Returns:
        A :class:`SplitResult` with one :class:`SplitBucket` per prefix
        plus a ``remainder`` bucket for unmatched diffs.
    """
    if result is None:
        raise SplitError("result must not be None")
    if not prefixes:
        raise SplitError("at least one prefix is required")

    split = SplitResult(buckets={p: SplitBucket(p) for p in prefixes})

    all_diffs: List[KeyDiff] = (
        list(result.diffs) if hasattr(result, "diffs") else
        [*result.missing_in_right, *result.missing_in_left, *result.mismatched]
    )

    for diff in all_diffs:
        placed = False
        for prefix in prefixes:
            if use_glob:
                matched = fnmatch(diff.key, prefix)
            else:
                matched = diff.key.startswith(prefix + separator) or diff.key == prefix
            if matched:
                split.buckets[prefix].diffs.append(diff)
                placed = True
                break
        if not placed:
            split.remainder.diffs.append(diff)

    return split
