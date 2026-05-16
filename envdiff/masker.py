"""masker.py – selectively mask values in a parsed env dict before display or export.

A MaskOptions controls which keys are masked and what the replacement looks like.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_DEFAULT_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api_key|apikey|auth|credential|private_key|access_key)"
]

MASK_PLACEHOLDER = "***"


class MaskError(Exception):
    """Raised when masker configuration is invalid."""


@dataclass
class MaskOptions:
    patterns: List[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))
    placeholder: str = MASK_PLACEHOLDER
    extra_keys: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        compiled = []
        for p in self.patterns:
            try:
                compiled.append(re.compile(p))
            except re.error as exc:
                raise MaskError(f"Invalid mask pattern {p!r}: {exc}") from exc
        self._compiled: List[re.Pattern[str]] = compiled

    def should_mask(self, key: str) -> bool:
        if key in self.extra_keys:
            return True
        return any(rx.search(key) for rx in self._compiled)


@dataclass
class MaskResult:
    original: Dict[str, str]
    masked: Dict[str, str]
    masked_keys: List[str]

    @property
    def mask_count(self) -> int:
        return len(self.masked_keys)


def mask_env(
    env: Dict[str, str],
    options: Optional[MaskOptions] = None,
) -> MaskResult:
    """Return a copy of *env* with sensitive values replaced by the placeholder."""
    if env is None:
        raise MaskError("env dict must not be None")
    opts = options or MaskOptions()
    masked: Dict[str, str] = {}
    masked_keys: List[str] = []
    for key, value in env.items():
        if opts.should_mask(key):
            masked[key] = opts.placeholder
            masked_keys.append(key)
        else:
            masked[key] = value
    return MaskResult(original=dict(env), masked=masked, masked_keys=sorted(masked_keys))
