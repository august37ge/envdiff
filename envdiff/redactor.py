"""Redactor: mask sensitive values in a parsed env dict before display or export."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should be redacted by default
_DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth|credential|cert)"
]

REDACTED_PLACEHOLDER = "***REDACTED***"


class RedactError(Exception):
    """Raised when redaction configuration is invalid."""


@dataclass
class RedactOptions:
    """Options controlling which keys are redacted."""

    patterns: List[str] = field(default_factory=lambda: list(_DEFAULT_SENSITIVE_PATTERNS))
    extra_keys: List[str] = field(default_factory=list)
    placeholder: str = REDACTED_PLACEHOLDER

    def __post_init__(self) -> None:
        for pat in self.patterns:
            try:
                re.compile(pat)
            except re.error as exc:
                raise RedactError(f"Invalid redact pattern {pat!r}: {exc}") from exc


def _is_sensitive(key: str, options: RedactOptions) -> bool:
    """Return True if *key* matches any sensitive pattern or is in extra_keys."""
    if key in options.extra_keys:
        return True
    for pat in options.patterns:
        if re.search(pat, key):
            return True
    return False


def redact(env: Dict[str, str], options: Optional[RedactOptions] = None) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by the placeholder.

    Args:
        env: Mapping of key -> value as returned by ``parse_env_file``.
        options: Redaction configuration; defaults to :class:`RedactOptions`.

    Returns:
        New dict with sensitive values masked.
    """
    if options is None:
        options = RedactOptions()
    return {
        key: (options.placeholder if _is_sensitive(key, options) else value)
        for key, value in env.items()
    }
