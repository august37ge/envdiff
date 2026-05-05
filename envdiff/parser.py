"""Parser for .env files."""

from pathlib import Path
from typing import Dict, Optional


class EnvParseError(Exception):
    """Raised when a .env file cannot be parsed."""
    pass


def parse_env_file(filepath: str | Path) -> Dict[str, Optional[str]]:
    """Parse a .env file and return a dict of key-value pairs.

    Supports:
    - KEY=VALUE
    - KEY="VALUE" or KEY='VALUE' (quotes stripped)
    - # comments (ignored)
    - blank lines (ignored)
    - keys with no value (KEY= or KEY with no '=')

    Args:
        filepath: Path to the .env file.

    Returns:
        Dictionary mapping variable names to their string values (or None).

    Raises:
        EnvParseError: If the file cannot be read or contains invalid syntax.
    """
    path = Path(filepath)
    if not path.exists():
        raise EnvParseError(f"File not found: {filepath}")
    if not path.is_file():
        raise EnvParseError(f"Not a file: {filepath}")

    env_vars: Dict[str, Optional[str]] = {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EnvParseError(f"Could not read file: {filepath}") from exc

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            # Treat bare keys as keys with no value
            key = line.strip()
            if not _is_valid_key(key):
                raise EnvParseError(
                    f"Invalid key '{key}' at line {lineno} in {filepath}"
                )
            env_vars[key] = None
            continue

        key, _, value = line.partition("=")
        key = key.strip()

        if not _is_valid_key(key):
            raise EnvParseError(
                f"Invalid key '{key}' at line {lineno} in {filepath}"
            )

        value = value.strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[0] == value[-1]:
            value = value[1:-1]

        env_vars[key] = value if value != "" else None

    return env_vars


def _is_valid_key(key: str) -> bool:
    """Return True if the key is a valid environment variable name."""
    if not key:
        return False
    return all(c.isalnum() or c == "_" for c in key) and not key[0].isdigit()
