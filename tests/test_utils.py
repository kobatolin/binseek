"""Tests for UI utility helpers."""

from __future__ import annotations

import pytest

from binseek.ui.utils import parse_pattern


def test_parse_text_pattern() -> None:
    assert parse_pattern("Hello", hex_mode=False) == b"Hello"


def test_parse_hex_pattern() -> None:
    assert parse_pattern("48 65 6C 6C 6F", hex_mode=True) == b"Hello"
    assert parse_pattern("48656C6C6F", hex_mode=True) == b"Hello"


def test_parse_escape_pattern() -> None:
    assert parse_pattern("a\\tb\\n", hex_mode=False, escape=True) == b"a\tb\n"
    assert parse_pattern("\\r\\n\\0", hex_mode=False, escape=True) == b"\r\n\0"
    assert parse_pattern("\\\\", hex_mode=False, escape=True) == b"\\"
    assert parse_pattern("\\x41\\x42", hex_mode=False, escape=True) == b"AB"


def test_parse_escape_invalid() -> None:
    with pytest.raises(ValueError):
        parse_pattern("\\q", hex_mode=False, escape=True)
    with pytest.raises(ValueError):
        parse_pattern("\\xZZ", hex_mode=False, escape=True)


def test_parse_escape_disabled_ignores_backslash() -> None:
    assert parse_pattern("a\\tb", hex_mode=False, escape=False) == b"a\\tb"
