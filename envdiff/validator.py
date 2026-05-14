"""Validation utilities for envdiff — checks env files for common issues."""

from dataclasses import dataclass, field
from typing import List

from envdiff.parser import EnvParseError, parse_env_file


@dataclass
class ValidationIssue:
    line_number: int
    line: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.message!r} -> {self.line!r}"


@dataclass
class ValidationResult:
    path: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.is_valid:
            return f"{self.path}: OK"
        lines = [f"{self.path}: {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def validate_env_file(path: str) -> ValidationResult:
    """Validate an env file for parse errors and common issues."""
    result = ValidationResult(path=path)

    try:
        raw_lines = _read_lines(path)
    except OSError as exc:
        result.issues.append(ValidationIssue(0, "", f"Cannot read file: {exc}"))
        return result

    seen_keys: dict = {}

    for lineno, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(
                ValidationIssue(lineno, line, "Missing '=' separator")
            )
            continue

        key, _, value = line.partition("=")
        key = key.strip()

        if not key:
            result.issues.append(
                ValidationIssue(lineno, line, "Empty key")
            )
            continue

        if " " in key:
            result.issues.append(
                ValidationIssue(lineno, line, "Key contains whitespace")
            )

        if key in seen_keys:
            result.issues.append(
                ValidationIssue(
                    lineno,
                    line,
                    f"Duplicate key '{key}' (first defined on line {seen_keys[key]})",
                )
            )
        else:
            seen_keys[key] = lineno

        value = value.strip()
        if value and value[0] in ('"', "'") and (
            len(value) < 2 or value[-1] != value[0]
        ):
            result.issues.append(
                ValidationIssue(lineno, line, "Unclosed quote in value")
            )

    return result


def _read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.readlines()
