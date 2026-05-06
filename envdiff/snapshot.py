"""Snapshot support: save and load env comparison results to/from JSON files."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from envdiff.comparator import CompareResult, KeyDiff


class SnapshotError(Exception):
    """Raised when a snapshot cannot be saved or loaded."""


def save_snapshot(
    result: CompareResult,
    path: str,
    left_name: str = "left",
    right_name: str = "right",
) -> None:
    """Persist a CompareResult to *path* as a JSON snapshot."""
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "left": left_name,
        "right": right_name,
        "missing_in_left": list(result.missing_in_left),
        "missing_in_right": list(result.missing_in_right),
        "mismatched": [
            {"key": d.key, "left_value": d.left_value, "right_value": d.right_value}
            for d in result.mismatched
        ],
    }
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except OSError as exc:
        raise SnapshotError(f"Cannot write snapshot to '{path}': {exc}") from exc


def load_snapshot(path: str) -> tuple[CompareResult, dict]:
    """Load a CompareResult from a JSON snapshot file.

    Returns a tuple of (CompareResult, metadata) where metadata contains
    ``created_at``, ``left``, and ``right`` keys.
    """
    if not os.path.isfile(path):
        raise SnapshotError(f"Snapshot file not found: '{path}'")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Cannot read snapshot from '{path}': {exc}") from exc

    mismatched = [
        KeyDiff(
            key=entry["key"],
            left_value=entry["left_value"],
            right_value=entry["right_value"],
        )
        for entry in payload.get("mismatched", [])
    ]
    result = CompareResult(
        missing_in_left=set(payload.get("missing_in_left", [])),
        missing_in_right=set(payload.get("missing_in_right", [])),
        mismatched=mismatched,
    )
    meta = {
        "created_at": payload.get("created_at"),
        "left": payload.get("left"),
        "right": payload.get("right"),
    }
    return result, meta
