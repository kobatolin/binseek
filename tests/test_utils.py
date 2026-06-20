"""Tests for UI utility helpers."""

from __future__ import annotations

import pytest

from binseek.ui.utils import parse_pattern


def test_parse_text_pattern() -> None:
    assert parse_pattern("Hello", hex_mode=False) == b"Hello"


def test_parse_hex_pattern() -> None:
    assert parse_pattern("48 65 6C 6C 6F", hex_mode=True) == b"Hello"
    assert parse_pattern("48656C6C6F", hex_mode=True) == b"Hello"


def test_parse_hex_invalid() -> None:
    with pytest.raises(ValueError):
        parse_pattern("486", hex_mode=True)
    with pytest.raises(ValueError):
        parse_pattern("ZZ", hex_mode=True)
