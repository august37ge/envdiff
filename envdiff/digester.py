"""digester.py – compute a deterministic digest (fingerprint) of a parsed .env file.

The digest is a SHA-256 hex string derived from the sorted key=value pairs so
that two files with the same logical content always produce the same digest,
regardless of comment lines, blank lines, or key ordering.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from envdiff.parser import parse_env_file, EnvParseError


class DigestError(Exception):
    """Raised when a digest cannot be computed."""


@dataclass(frozen=True)
class DigestResult:
    path: Path
    digest: str          # hex SHA-256
    key_count: int

    def __str__(self) -> str:
        return f"{self.path}: {self.digest} ({self.key_count} keys)"


def _canonical_bytes(env: Dict[str, str]) -> bytes:
    """Return a stable byte representation of *env* for hashing."""
    lines = [f"{k}={env[k]}" for k in sorted(env)]
    return "\n".join(lines).encode()


def digest_file(path: str | Path) -> DigestResult:
    """Parse *path* and return a :class:`DigestResult`.

    Raises
    ------
    DigestError
        If the file cannot be read or parsed.
    """
    resolved = Path(path)
    if not resolved.exists():
        raise DigestError(f"File not found: {resolved}")
    try:
        env = parse_env_file(resolved)
    except EnvParseError as exc:
        raise DigestError(str(exc)) from exc

    raw = _canonical_bytes(env)
    hex_digest = hashlib.sha256(raw).hexdigest()
    return DigestResult(path=resolved, digest=hex_digest, key_count=len(env))


def digests_match(left: str | Path, right: str | Path) -> bool:
    """Return *True* when both files produce the same digest."""
    return digest_file(left).digest == digest_file(right).digest
