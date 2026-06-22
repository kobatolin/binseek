"""Small UI helpers."""

from __future__ import annotations


_ESCAPE_SEQUENCES = {
    "\\t": b"\t",
    "\\n": b"\n",
    "\\r": b"\r",
    "\\0": b"\0",
    "\\\\": b"\\",
}


def _decode_escape(text: str) -> bytes:
    out = bytearray()
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            seq = text[i : i + 2]
            if seq in _ESCAPE_SEQUENCES:
                out.extend(_ESCAPE_SEQUENCES[seq])
                i += 2
                continue
            if text[i + 1] == "x" and i + 3 < len(text):
                try:
                    value = int(text[i + 2 : i + 4], 16)
                except ValueError:
                    raise ValueError(f"invalid hex escape at position {i}") from None
                out.append(value)
                i += 4
                continue
            raise ValueError(f"invalid escape sequence at position {i}: {seq!r}")
        out.extend(text[i].encode("utf-8", errors="replace"))
        i += 1
    return bytes(out)


def parse_pattern(text: str, hex_mode: bool, escape: bool = False) -> bytes:
    """Parse a user-entered pattern into bytes."""
    if hex_mode:
        cleaned = "".join(text.split())
        if len(cleaned) % 2 != 0:
            raise ValueError("hex pattern must have an even number of digits")
        if not all(c in "0123456789abcdefABCDEF" for c in cleaned):
            raise ValueError("invalid hex digits")
        return bytes.fromhex(cleaned)
    if escape:
        return _decode_escape(text)
    return text.encode("utf-8", errors="replace")


def format_offset(offset: int) -> str:
    return f"0x{offset:08X}"
