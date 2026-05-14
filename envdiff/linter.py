"""Linter for .env files: checks style and convention issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file, EnvParseError


class LintError(Exception):
    """Raised when linting cannot proceed."""


@dataclass
class LintIssue:
    line_number: int
    key: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line_number} [{self.code}] {self.key!r}: {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_clean:
            return f"{self.path}: no lint issues"
        lines = [f"{self.path}:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


_UPPER_SNAKE_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_DOUBLE_UNDERSCORE_RE = re.compile(r'__')


def lint_file(path: str) -> LintResult:
    """Lint a single .env file and return a LintResult."""
    p = Path(path)
    if not p.exists():
        raise LintError(f"File not found: {path}")

    try:
        _ = parse_env_file(path)  # ensure parseable
    except EnvParseError as exc:
        raise LintError(str(exc)) from exc

    result = LintResult(path=path)
    raw_lines = p.read_text(encoding="utf-8").splitlines()

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()

        # E001: key should be UPPER_SNAKE_CASE
        if not _UPPER_SNAKE_RE.match(key):
            result.issues.append(LintIssue(
                line_number=lineno,
                key=key,
                code="E001",
                message="Key should be UPPER_SNAKE_CASE",
            ))

        # E002: double underscores in key
        if _DOUBLE_UNDERSCORE_RE.search(key):
            result.issues.append(LintIssue(
                line_number=lineno,
                key=key,
                code="E002",
                message="Key contains double underscores",
            ))

        # W001: value contains unquoted whitespace
        val = value.strip()
        if val and not (val.startswith('"') or val.startswith("'")):
            if " " in val or "\t" in val:
                result.issues.append(LintIssue(
                    line_number=lineno,
                    key=key,
                    code="W001",
                    message="Value with spaces should be quoted",
                ))

    return result
