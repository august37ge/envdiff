"""Apply a diff result as patches to produce a merged .env file."""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.comparator import CompareResult
from envdiff.parser import parse_env_file


class PatchError(Exception):
    """Raised when patching fails."""


@dataclasses.dataclass
class PatchOptions:
    """Controls how patches are applied."""
    fill_missing: bool = True       # add keys missing in base from other
    overwrite_mismatches: bool = False  # replace base values with other on mismatch
    comment_source: bool = False    # annotate added/changed lines with a comment


@dataclasses.dataclass
class PatchResult:
    """Result of a patch operation."""
    patched: Dict[str, str]
    added_keys: List[str]
    changed_keys: List[str]

    @property
    def has_changes(self) -> bool:
        return bool(self.added_keys or self.changed_keys)

    def __str__(self) -> str:  # pragma: no cover
        lines = []
        for key, val in self.patched.items():
            lines.append(f"{key}={val}")
        return "\n".join(lines)


def patch_result(
    base_path: Path,
    other_path: Path,
    compare: CompareResult,
    options: Optional[PatchOptions] = None,
) -> PatchResult:
    """Produce a patched env dict from *base_path* using *compare* and *other_path*."""
    if options is None:
        options = PatchOptions()

    base = parse_env_file(base_path)
    other = parse_env_file(other_path)

    patched: Dict[str, str] = dict(base)
    added: List[str] = []
    changed: List[str] = []

    if options.fill_missing:
        for key in compare.missing_in_left:
            patched[key] = other.get(key, "")
            added.append(key)

    if options.overwrite_mismatches:
        for diff in compare.mismatches:
            patched[diff.key] = diff.right_value or ""
            changed.append(diff.key)

    return PatchResult(patched=patched, added_keys=added, changed_keys=changed)


def write_patch(result: PatchResult, dest: Path, options: Optional[PatchOptions] = None) -> None:
    """Write *result.patched* to *dest* as a .env file."""
    if options is None:
        options = PatchOptions()
    try:
        lines: List[str] = []
        for key, val in result.patched.items():
            if options.comment_source and key in result.added_keys:
                lines.append(f"# added by envdiff patcher")
            elif options.comment_source and key in result.changed_keys:
                lines.append(f"# updated by envdiff patcher")
            lines.append(f"{key}={val}")
        dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        raise PatchError(f"Cannot write patch to {dest}: {exc}") from exc
