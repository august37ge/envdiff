"""Baseline comparison: diff a .env file against a saved snapshot baseline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envdiff.comparator import CompareResult
from envdiff.differ import diff_files
from envdiff.snapshot import load_snapshot, SnapshotError


class BaselineError(Exception):
    """Raised when a baseline comparison cannot be completed."""


@dataclass
class BaselineResult:
    """Outcome of comparing a live .env file against a stored baseline snapshot."""

    baseline_path: Path
    env_path: Path
    compare: CompareResult

    @property
    def has_diffs(self) -> bool:
        return self.compare.has_diffs

    def summary(self) -> str:
        lines = [
            f"Baseline : {self.baseline_path}",
            f"Live file: {self.env_path}",
        ]
        if not self.has_diffs:
            lines.append("Status   : in sync")
        else:
            m_right = len(self.compare.missing_in_right)
            m_left = len(self.compare.missing_in_left)
            mm = len(self.compare.mismatched)
            lines.append(
                f"Status   : drifted "
                f"(+{m_left} added, -{m_right} removed, ~{mm} changed)"
            )
        return "\n".join(lines)


def diff_against_baseline(
    env_path: str | Path,
    baseline_path: str | Path,
    keys_only: bool = False,
) -> BaselineResult:
    """Compare *env_path* against a previously saved snapshot at *baseline_path*.

    The snapshot is loaded into a temporary file so the standard diff pipeline
    can be reused without duplication.
    """
    env_path = Path(env_path)
    baseline_path = Path(baseline_path)

    if not env_path.exists():
        raise BaselineError(f"Env file not found: {env_path}")
    if not baseline_path.exists():
        raise BaselineError(f"Baseline snapshot not found: {baseline_path}")

    try:
        snapshot_result = load_snapshot(baseline_path)
    except SnapshotError as exc:
        raise BaselineError(f"Failed to load baseline: {exc}") from exc

    # Reconstruct a temporary env file from the snapshot's left-side data
    import tempfile, json

    raw = json.loads(baseline_path.read_text())
    left_env: dict[str, str] = raw.get("left", {})

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".env", delete=False
    ) as tmp:
        for k, v in left_env.items():
            tmp.write(f"{k}={v}\n")
        tmp_path = Path(tmp.name)

    try:
        compare = diff_files(str(tmp_path), str(env_path), keys_only=keys_only)
    finally:
        tmp_path.unlink(missing_ok=True)

    return BaselineResult(
        baseline_path=baseline_path,
        env_path=env_path,
        compare=compare,
    )
