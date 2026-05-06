"""High-level diff orchestration: parse two env files and return a CompareResult."""

from pathlib import Path
from typing import Union

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare, CompareResult
from envdiff.validator import validate_file, ValidationResult


class DiffError(Exception):
    """Raised when a diff cannot be completed due to parse or validation issues."""


def diff_files(
    left: Union[str, Path],
    right: Union[str, Path],
    keys_only: bool = False,
    validate: bool = False,
) -> CompareResult:
    """Parse *left* and *right* env files and return a :class:`CompareResult`.

    Parameters
    ----------
    left:
        Path to the first (reference) env file.
    right:
        Path to the second env file.
    keys_only:
        When ``True`` only key presence is compared; values are ignored.
    validate:
        When ``True`` both files are validated before diffing; a
        :class:`DiffError` is raised if either file has issues.
    """
    left = Path(left)
    right = Path(right)

    for path in (left, right):
        if not path.exists():
            raise DiffError(f"File not found: {path}")

    if validate:
        for path in (left, right):
            result: ValidationResult = validate_file(path)
            if not result.is_valid:
                issues = "; ".join(str(i) for i in result.issues)
                raise DiffError(f"Validation failed for {path}: {issues}")

    try:
        left_env = parse_env_file(left)
        right_env = parse_env_file(right)
    except EnvParseError as exc:
        raise DiffError(str(exc)) from exc

    return compare(left_env, right_env, keys_only=keys_only)
