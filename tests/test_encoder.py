"""Tests for envdiff.encoder."""
import json
import pytest
from envdiff.encoder import EncodeError, EncodeOptions, encode


SIMPLE = {"FOO": "bar", "BAZ": "qux"}


# ---------------------------------------------------------------------------
# dotenv format
# ---------------------------------------------------------------------------

def test_dotenv_basic():
    out = encode({"KEY": "value"})
    assert "KEY=value" in out


def test_dotenv_sort_keys():
    out = encode({"Z": "1", "A": "2"}, EncodeOptions(sort_keys=True))
    lines = [l for l in out.splitlines() if l]
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_dotenv_quote_all():
    out = encode({"K": "v"}, EncodeOptions(quote_all=True))
    assert 'K="v"' in out


def test_dotenv_auto_quotes_space():
    out = encode({"K": "hello world"})
    assert 'K="hello world"' in out


def test_dotenv_auto_quotes_hash():
    out = encode({"K": "val#comment"})
    assert '"' in out


def test_dotenv_include_export():
    out = encode({"PORT": "8080"}, EncodeOptions(include_export=True))
    assert out.strip() == 'export PORT=8080'


def test_dotenv_export_format_shortcut():
    out = encode({"X": "1"}, EncodeOptions(fmt="export"))
    assert out.strip() == "export X=1"


def test_dotenv_ends_with_newline():
    out = encode({"A": "1"})
    assert out.endswith("\n")


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def test_json_is_valid():
    out = encode(SIMPLE, EncodeOptions(fmt="json"))
    parsed = json.loads(out)
    assert parsed == SIMPLE


def test_json_sorted_keys():
    out = encode({"Z": "1", "A": "2"}, EncodeOptions(fmt="json", sort_keys=True))
    keys = list(json.loads(out).keys())
    assert keys == ["A", "Z"]


# ---------------------------------------------------------------------------
# YAML format
# ---------------------------------------------------------------------------

def test_yaml_basic():
    out = encode({"HOST": "localhost"}, EncodeOptions(fmt="yaml"))
    assert "HOST: localhost" in out


def test_yaml_quotes_value_with_space():
    out = encode({"MSG": "hello world"}, EncodeOptions(fmt="yaml"))
    assert 'MSG: "hello world"' in out


def test_yaml_empty_value_quoted():
    out = encode({"EMPTY": ""}, EncodeOptions(fmt="yaml"))
    assert 'EMPTY: ""' in out


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_none_env_raises():
    with pytest.raises(EncodeError):
        encode(None)  # type: ignore


def test_unknown_format_raises():
    with pytest.raises(EncodeError, match="Unknown format"):
        encode({"K": "v"}, EncodeOptions(fmt="xml"))  # type: ignore
