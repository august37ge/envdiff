"""Interactive side-by-side diff presenter for two .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.differ import diff_files


class InteractiveDiffError(Exception):
    """Raised when the interactive diff cannot be produced."""


@dataclass
class SideBySideRow:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]
    status: str  # 'ok' | 'missing_left' | 'missing_right' | 'mismatch'

    def __str__(self) -> str:
        lv = self.left_value if self.left_value is not None else "<absent>"
        rv = self.right_value if self.right_value is not None else "<absent>"
        return f"{self.key:<30}  {lv:<25}  {rv:<25}  [{self.status}]"


@dataclass
class SideBySideResult:
    left_path: str
    right_path: str
    rows: List[SideBySideRow] = field(default_factory=list)

    @property
    def has_diffs(self) -> bool:
        return any(r.status != "ok" for r in self.rows)

    def rows_with_status(self, status: str) -> List[SideBySideRow]:
        return [r for r in self.rows if r.status == status]


def build_side_by_side(result: CompareResult, left_path: str, right_path: str) -> SideBySideResult:
    """Convert a CompareResult into a SideBySideResult."""
    if result is None:
        raise InteractiveDiffError("result must not be None")

    diff_keys = {d.key: d for d in result.diffs}
    all_keys = sorted(
        set(result.left_only) | set(result.right_only) | {d.key for d in result.diffs} |
        (set(result.shared_keys) if hasattr(result, "shared_keys") else set())
    )

    # Rebuild full key set from diffs and missing lists
    rows: List[SideBySideRow] = []
    missing_left = set(result.missing_in_left)
    missing_right = set(result.missing_in_right)

    for key in all_keys:
        if key in missing_left:
            rows.append(SideBySideRow(key=key, left_value=None, right_value=None, status="missing_left"))
        elif key in missing_right:
            rows.append(SideBySideRow(key=key, left_value=None, right_value=None, status="missing_right"))
        elif key in diff_keys:
            d = diff_keys[key]
            rows.append(SideBySideRow(key=key, left_value=d.left_value, right_value=d.right_value, status="mismatch"))
        else:
            rows.append(SideBySideRow(key=key, left_value=None, right_value=None, status="ok"))

    return SideBySideResult(left_path=left_path, right_path=right_path, rows=rows)


def diff_interactive(left: str, right: str) -> SideBySideResult:
    """Parse two .env files and return a SideBySideResult."""
    try:
        result = diff_files(left, right)
    except Exception as exc:
        raise InteractiveDiffError(str(exc)) from exc
    return build_side_by_side(result, left, right)
