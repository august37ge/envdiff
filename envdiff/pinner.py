"""Pin the current state of an env file as a baseline for future comparisons."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from envdiff.parser import parse_env_file


class PinError(Exception):
    """Raised when a pin operation fails."""


@dataclass
class PinEntry:
    path: str
    pinned_at: str
    values: Dict[str, str]

    def to_dict(self) -> dict:
        return {"path": self.path, "pinned_at": self.pinned_at, "values": self.values}

    @classmethod
    def from_dict(cls, data: dict) -> "PinEntry":
        return cls(
            path=data["path"],
            pinned_at=data["pinned_at"],
            values=data["values"],
        )


def pin_file(env_path: str) -> PinEntry:
    """Parse *env_path* and return a PinEntry capturing its current state."""
    p = Path(env_path)
    if not p.is_file():
        raise PinError(f"File not found: {env_path}")
    values = parse_env_file(str(p))
    return PinEntry(
        path=str(p.resolve()),
        pinned_at=datetime.now(timezone.utc).isoformat(),
        values=values,
    )


def save_pin(entry: PinEntry, output_path: str) -> None:
    """Write *entry* as JSON to *output_path*."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")


def load_pin(pin_path: str) -> PinEntry:
    """Load a previously saved PinEntry from *pin_path*."""
    p = Path(pin_path)
    if not p.is_file():
        raise PinError(f"Pin file not found: {pin_path}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return PinEntry.from_dict(data)
    except (KeyError, json.JSONDecodeError) as exc:
        raise PinError(f"Invalid pin file: {exc}") from exc


def diff_against_pin(env_path: str, entry: PinEntry) -> dict:
    """Compare the current state of *env_path* against a saved *entry*.

    Returns a dict with keys 'added', 'removed', 'changed'.
    """
    p = Path(env_path)
    if not p.is_file():
        raise PinError(f"File not found: {env_path}")
    current = parse_env_file(str(p))
    pinned = entry.values

    added = {k: current[k] for k in current if k not in pinned}
    removed = {k: pinned[k] for k in pinned if k not in current}
    changed = {
        k: {"pinned": pinned[k], "current": current[k]}
        for k in current
        if k in pinned and current[k] != pinned[k]
    }
    return {"added": added, "removed": removed, "changed": changed}
