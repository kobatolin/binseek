"""Tests for the high-level buffer model."""

from __future__ import annotations

import os
import tempfile

import pytest

from binseek.core._native import CoreError
from binseek.model.buffer import Buffer


@pytest.fixture
def sample_path() -> str:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Hello world! This is a test file for binseek.")
        path = f.name
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


def test_open_and_read(sample_path: str) -> None:
    buf = Buffer.open(sample_path)
    assert buf.size == 45
    assert buf.read(0, 5) == b"Hello"
    assert buf.read(6, 5) == b"world"
    assert not buf.dirty
    buf.close()


def test_search(sample_path: str) -> None:
    buf = Buffer.open(sample_path)
    results = buf.search(b"Hello")
    assert results == [(0, 5)]
    results = buf.search(b" ")
    assert results == [
        (5, 1),
        (12, 1),
        (17, 1),
        (20, 1),
        (22, 1),
        (27, 1),
        (32, 1),
        (36, 1),
    ]
    results = buf.search(b"hello", case_insensitive=True)
    assert results == [(0, 5)]
    results = buf.search(b"HELLO", case_insensitive=True)
    assert results == [(0, 5)]
    buf.close()


def test_replace_overwrite(sample_path: str) -> None:
    buf = Buffer.open(sample_path)
    buf.replace(0, 5, b"Hallo")
    assert buf.dirty
    assert buf.read(0, 5) == b"Hallo"
    assert buf.size == 45
    with tempfile.NamedTemporaryFile(delete=False) as out:
        out_path = out.name
    buf.save(out_path)
    with open(out_path, "rb") as f:
        assert f.read(5) == b"Hallo"
    os.unlink(out_path)
    buf.close()


def test_replace_insert_and_delete(sample_path: str) -> None:
    buf = Buffer.open(sample_path)
    buf.replace(5, 0, b"XX")  # insert
    assert buf.read(5, 7) == b"XX worl"
    assert buf.size == 47
    buf.replace(5, 2, b"")  # delete inserted bytes
    assert buf.size == 45
    assert buf.read(5, 6) == b" world"
    buf.close()


def test_open_missing_file() -> None:
    with pytest.raises(CoreError):
        Buffer.open("/nonexistent/path/for/binseek/test.bin")


def test_search_regex_ascii(sample_path: str) -> None:
    buf = Buffer.open(sample_path)
    results = buf.search_regex(r"H.llo", hex_mode=False)
    assert results == [(0, 5)]
    results = buf.search_regex(r"wor\w+", hex_mode=False)
    assert results == [(6, 5)]
    results = buf.search_regex(r"HELLO", hex_mode=False, case_insensitive=True)
    assert results == [(0, 5)]
    buf.close()


def test_search_regex_hex(sample_path: str) -> None:
    buf = Buffer.open(sample_path)
    results = buf.search_regex("48 65 6C 6C 6F", hex_mode=True)
    assert results == [(0, 5)]
    results = buf.search_regex("48 ? 6C 6C", hex_mode=True)
    assert results == [(0, 4)]
    results = buf.search_regex("6.", hex_mode=True)
    assert len(results) >= 2
    buf.close()


def test_search_regex_hex_invalid(sample_path: str) -> None:
    buf = Buffer.open(sample_path)
    with pytest.raises(CoreError):
        buf.search_regex("[", hex_mode=True)
    buf.close()
