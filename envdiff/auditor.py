"""Audit .env files for sensitive key patterns and common security issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file

# Patterns that commonly indicate sensitive values
_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(password|passwd|pwd)", re.IGNORECASE),
    re.compile(r"(secret|token|api_key|apikey)", re.IGNORECASE),
    re.compile(r"(private_key|privkey)", re.IGNORECASE),
    re.compile(r"(auth|credential)", re.IGNORECASE),
]

# Patterns that indicate a value looks like a plaintext secret (not a reference)
_PLAINTEXT_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9+/=_\-]{8,}$")


class AuditError(Exception):
    """Raised when auditing cannot be completed."""


@dataclass
class AuditIssue:
    key: str
    message: str
    severity: str  # "warn" | "info"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class AuditResult:
    path: Path
    issues: List[AuditIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def warnings(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "warn"]

    @property
    def infos(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "info"]


def audit_file(path: Path) -> AuditResult:
    """Audit a single .env file and return an AuditResult."""
    if not path.exists():
        raise AuditError(f"File not found: {path}")

    env = parse_env_file(path)
    result = AuditResult(path=path)

    for key, value in env.items():
        _check_key(key, value, result)

    return result


def _check_key(key: str, value: str, result: AuditResult) -> None:
    is_sensitive = any(p.search(key) for p in _SENSITIVE_PATTERNS)

    if is_sensitive and value == "":
        result.issues.append(
            AuditIssue(key=key, message="Sensitive key has an empty value.", severity="warn")
        )
        return

    if is_sensitive and _PLAINTEXT_VALUE_PATTERN.match(value):
        result.issues.append(
            AuditIssue(
                key=key,
                message="Sensitive key may contain a plaintext secret.",
                severity="warn",
            )
        )

    if not is_sensitive and value == "":
        result.issues.append(
            AuditIssue(key=key, message="Key has an empty value.", severity="info")
        )
