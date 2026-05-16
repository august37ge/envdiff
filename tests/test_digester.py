"""Tests for envdiff.digester."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.digester import digest_file, digests_match, DigestError


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_digest_returns_64_char_hex(tmp_path):
    f = _write(tmp_path, ".env", "KEY=value\n")
    result = digest_file(f)
    assert len(result.digest) == 64
    assert all(c in "0123456789abcdef" for c in result.digest)


def test_key_count_correct(tmp_path):
    f = _write(tmp_path, ".env", "A=1\nB=2\nC=3\n")
    result = digest_file(f)
    assert result.key_count == 3


def test_comments_and_blanks_ignored_in_digest(tmp_path):
    clean = _write(tmp_path, "clean.env", "KEY=val\n")
    noisy = _write(tmp_path, "noisy.env", "# comment\n\nKEY=val\n")
    assert digest_file(clean).digest == digest_file(noisy).digest


def test_key_order_does_not_affect_digest(tmp_path):
    f1 = _write(tmp_path, "a.env", "A=1\nB=2\n")
    f2 = _write(tmp_path, "b.env", "B=2\nA=1\n")
    assert digest_file(f1).digest == digest_file(f2).digest


def test_different_values_produce_different_digest(tmp_path):
    f1 = _write(tmp_path, "a.env", "KEY=foo\n")
    f2 = _write(tmp_path, "b.env", "KEY=bar\n")
    assert digest_file(f1).digest != digest_file(f2).digest


def test_missing_file_raises_digest_error(tmp_path):
    with pytest.raises(DigestError, match="not found"):
        digest_file(tmp_path / "ghost.env")


def test_digests_match_true_for_equivalent_files(tmp_path):
    f1 = _write(tmp_path, "a.env", "X=1\nY=2\n")
    f2 = _write(tmp_path, "b.env", "Y=2\nX=1\n")
    assert digests_match(f1, f2) is True


def test_digests_match_false_for_different_files(tmp_path):
    f1 = _write(tmp_path, "a.env", "X=1\n")
    f2 = _write(tmp_path, "b.env", "X=2\n")
    assert digests_match(f1, f2) is False


def test_str_representation_contains_path_and_key_count(tmp_path):
    f = _write(tmp_path, "sample.env", "FOO=bar\nBAZ=qux\n")
    result = digest_file(f)
    s = str(result)
    assert "sample.env" in s
    assert "2 keys" in s
