"""encoder.py – serialise a parsed env mapping to various output formats."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, Literal

OutputFormat = Literal["dotenv", "json", "export", "yaml"]


class EncodeError(ValueError):
    """Raised when encoding fails."""


@dataclass
class EncodeOptions:
    fmt: OutputFormat = "dotenv"
    sort_keys: bool = False
    quote_all: bool = False
    include_export: bool = False  # prefix each line with 'export ' (dotenv only)


def encode(env: Dict[str, str], options: EncodeOptions | None = None) -> str:
    """Encode *env* mapping to a string in the requested format."""
    if env is None:
        raise EncodeError("env mapping must not be None")
    opts = options or EncodeOptions()
    keys = sorted(env.keys()) if opts.sort_keys else list(env.keys())
    if opts.fmt == "dotenv":
        return _encode_dotenv(env, keys, opts)
    if opts.fmt == "json":
        return _encode_json(env, keys)
    if opts.fmt == "export":
        return _encode_dotenv(env, keys, EncodeOptions(include_export=True, sort_keys=opts.sort_keys, quote_all=opts.quote_all))
    if opts.fmt == "yaml":
        return _encode_yaml(env, keys)
    raise EncodeError(f"Unknown format: {opts.fmt!r}")


def _needs_quoting(value: str) -> bool:
    return any(ch in value for ch in (" ", "\t", "#", "'", '"', "$", "\n"))


def _encode_dotenv(env: Dict[str, str], keys: list, opts: EncodeOptions) -> str:
    lines: list[str] = []
    prefix = "export " if opts.include_export else ""
    for k in keys:
        v = env[k]
        if opts.quote_all or _needs_quoting(v):
            escaped = v.replace("\\", "\\\\").replace('"', '\\"')
            v = f'"{escaped}"'
        lines.append(f"{prefix}{k}={v}")
    return "\n".join(lines) + ("\n" if lines else "")


def _encode_json(env: Dict[str, str], keys: list) -> str:
    ordered = {k: env[k] for k in keys}
    return json.dumps(ordered, indent=2) + "\n"


def _encode_yaml(env: Dict[str, str], keys: list) -> str:
    lines: list[str] = []
    for k in keys:
        v = env[k]
        if _needs_quoting(v) or v == "":
            escaped = v.replace('"', '\\"')
            v = f'"{escaped}"'
        lines.append(f"{k}: {v}")
    return "\n".join(lines) + ("\n" if lines else "")
