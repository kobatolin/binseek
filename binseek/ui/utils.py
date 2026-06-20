"""Small UI helpers."""

from __future__ import annotations


def parse_pattern(text: str, hex_mode: bool) -> bytes:
    """Parse a user-entered pattern into bytes."""
    if hex_mode:
        cleaned = "".join(text.split())
        if len(cleaned) % 2 != 0:
            raise ValueError("hex pattern must have an even number of digits")
        if not all(c in "0123456789abcdefABCDEF" for c in cleaned):
            raise ValueError("invalid hex digits")
        return bytes.fromhex(cleaned)
    return text.encode("utf-8", errors="replace")


def format_offset(offset: int) -> str:
    return f"0x{offset:08X}"
