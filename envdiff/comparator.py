"""Core comparison logic for envdiff."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeyDiff:
    """Represents a difference found between two env files."""
    key: str
    status: str  # 'missing_in_left', 'missing_in_right', 'value_mismatch'
    left_value: Optional[str] = None
    right_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "missing_in_left":
            return f"  - {self.key!r} missing in left file (right={self.right_value!r})"
        elif self.status == "missing_in_right":
            return f"  - {self.key!r} missing in right file (left={self.left_value!r})"
        elif self.status == "value_mismatch":
            return (
                f"  ~ {self.key!r} value mismatch: "
                f"left={self.left_value!r}, right={self.right_value!r}"
            )
        return f"  ? {self.key!r} unknown diff status"


@dataclass
class CompareResult:
    """Result of comparing two env files."""
    left_path: str
    right_path: str
    diffs: List[KeyDiff] = field(default_factory=list)

    @property
    def has_diffs(self) -> bool:
        return len(self.diffs) > 0

    @property
    def missing_in_left(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "missing_in_left"]

    @property
    def missing_in_right(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "missing_in_right"]

    @property
    def mismatched(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "value_mismatch"]


def compare_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    left_path: str = "left",
    right_path: str = "right",
    keys_only: bool = False,
) -> CompareResult:
    """Compare two parsed env dicts and return a CompareResult.

    Args:
        left: Parsed env dict from the left/base file.
        right: Parsed env dict from the right/target file.
        left_path: Display path for the left file.
        right_path: Display path for the right file.
        keys_only: If True, skip value comparison (only check key presence).
    """
    result = CompareResult(left_path=left_path, right_path=right_path)

    all_keys = set(left) | set(right)

    for key in sorted(all_keys):
        in_left = key in left
        in_right = key in right

        if in_left and not in_right:
            result.diffs.append(
                KeyDiff(key=key, status="missing_in_right", left_value=left[key])
            )
        elif in_right and not in_left:
            result.diffs.append(
                KeyDiff(key=key, status="missing_in_left", right_value=right[key])
            )
        elif not keys_only and left[key] != right[key]:
            result.diffs.append(
                KeyDiff(
                    key=key,
                    status="value_mismatch",
                    left_value=left[key],
                    right_value=right[key],
                )
            )

    return result
