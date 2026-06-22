"""Large-file benchmark for binseek.

Creates a 1 GiB file containing big-endian 32-bit integers from 0x00000000
up to (and including) 0x0FFFFFFF, then exercises the C++ core through the
Python Buffer wrapper: open, search, replace, insert, larger replace, and
save-as.  Each step reports elapsed time and verifies correctness.
"""

from __future__ import annotations

import array
import os
import shutil
import struct
import sys
import tempfile
import time
from pathlib import Path

from binseek.model.buffer import Buffer

COUNT = 0x10000000  # 268,435,456 integers
ORIGINAL_SIZE = COUNT * 4  # 1,073,741,824 bytes (1 GiB)
CHUNK_INTS = 0x1000000  # 16,777,216 ints => 64 MiB per chunk
TARGET_VALUE = 0x00ABCDEF
TARGET_PATTERN = struct.pack(">I", TARGET_VALUE)
TARGET_OFFSET = TARGET_VALUE * 4


def generate_file(path: Path, count: int) -> float:
    """Write the test file and return elapsed seconds."""
    t0 = time.perf_counter()
    with open(path, "wb") as f:
        for start in range(0, count, CHUNK_INTS):
            end = min(start + CHUNK_INTS, count)
            arr = array.array("I", range(start, end))
            arr.byteswap()  # big-endian
            f.write(arr.tobytes())
    return time.perf_counter() - t0


def fmt_bytes(n: int) -> str:
    return f"{n:,} bytes ({n / (1024 ** 3):.3f} GiB)"


def main() -> int:
    tmp_dir = Path(tempfile.gettempdir()) / "binseek_large_test"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src = tmp_dir / "large_1gb.bin"
    saved = tmp_dir / "large_1gb_saved.bin"

    print(f"Working directory: {tmp_dir}")
    print(f"Target file size:  {fmt_bytes(ORIGINAL_SIZE)}")
    print()

    # 1. Generate file
    print("Generating test file...")
    gen_time = generate_file(src, COUNT)
    actual_size = src.stat().st_size
    print(f"  Generated in {gen_time:.3f}s")
    print(f"  Size on disk: {fmt_bytes(actual_size)}")
    assert actual_size == ORIGINAL_SIZE, f"expected {ORIGINAL_SIZE}, got {actual_size}"

    # Quick sanity check on disk format
    with open(src, "rb") as f:
        f.seek(TARGET_OFFSET)
        assert f.read(4) == TARGET_PATTERN
        f.seek((COUNT - 1) * 4)
        assert f.read(4) == b"\x0F\xFF\xFF\xFF"
    print("  Format sanity check passed")
    print()

    # 2. Open
    print("Opening with Buffer...")
    t0 = time.perf_counter()
    buf = Buffer.open(src)
    open_time = time.perf_counter() - t0
    print(f"  Opened in {open_time:.3f}s, reported size = {fmt_bytes(buf.size)}")
    assert buf.size == ORIGINAL_SIZE
    print()

    # 3. Search
    print(f"Searching for pattern {TARGET_PATTERN.hex().upper()} (value 0x{TARGET_VALUE:08X})...")
    t0 = time.perf_counter()
    results = buf.search(TARGET_PATTERN, max_results=5)
    search_time = time.perf_counter() - t0
    print(f"  Search completed in {search_time:.3f}s, hits = {len(results)}")
    assert len(results) == 1, f"expected 1 hit, got {len(results)}"
    offset, length = results[0]
    assert offset == TARGET_OFFSET, f"expected offset {TARGET_OFFSET:#x}, got {offset:#x}"
    assert length == len(TARGET_PATTERN)
    print(f"  Offset = 0x{offset:08X} (correct)")
    print()

    # 4. Replace a single 4-byte value in-place
    replace_offset = 0x00000040 * 4  # value 0x00000040
    replace_old_len = 4
    replace_new = b"\xDE\xAD\xBE\xEF"
    print(f"REPLACE at offset 0x{replace_offset:08X} (4 -> 4 bytes)...")
    t0 = time.perf_counter()
    buf.replace(replace_offset, replace_old_len, replace_new)
    replace_time = time.perf_counter() - t0
    print(f"  Replace completed in {replace_time:.3f}s")
    chunk = buf.read(replace_offset - 4, 12)
    expected = b"\x00\x00\x00\x3F" + replace_new + b"\x00\x00\x00\x41"
    assert chunk == expected, f"replace verify failed: {chunk.hex()} != {expected.hex()}"
    print(f"  In-memory verification passed")
    print()

    # 5. Insert 4 bytes at offset 0x200
    insert_offset = 0x200
    insert_data = b"\x11\x22\x33\x44"
    print(f"INSERT at offset 0x{insert_offset:08X} ({len(insert_data)} bytes)...")
    t0 = time.perf_counter()
    buf.replace(insert_offset, 0, insert_data)
    insert_time = time.perf_counter() - t0
    print(f"  Insert completed in {insert_time:.3f}s")
    assert buf.size == ORIGINAL_SIZE + len(insert_data)
    chunk = buf.read(insert_offset - 4, 12)
    expected = b"\x00\x00\x00\x7F" + insert_data + b"\x00\x00\x00\x80"
    assert chunk == expected, f"insert verify failed: {chunk.hex()} != {expected.hex()}"
    print(f"  In-memory verification passed, new size = {fmt_bytes(buf.size)}")
    print()

    # 6. Larger replace: 8 bytes -> 12 bytes at logical offset 0x304
    large_offset = 0x304
    large_old_len = 8
    large_new = b"\xAA\xBB\xCC\xDD\xEE\xFF\x00\x11\x22\x33\x44\x55"
    print(f"REPLACE at offset 0x{large_offset:08X} ({large_old_len} -> {len(large_new)} bytes)...")
    t0 = time.perf_counter()
    buf.replace(large_offset, large_old_len, large_new)
    large_replace_time = time.perf_counter() - t0
    print(f"  Replace completed in {large_replace_time:.3f}s")
    expected_final_size = ORIGINAL_SIZE + len(insert_data) + (len(large_new) - large_old_len)
    assert buf.size == expected_final_size
    chunk = buf.read(large_offset - 4, 20)
    expected = (
        b"\x00\x00\x00\xBF"
        + large_new
        + b"\x00\x00\x00\xC2"
    )
    assert chunk == expected, f"large replace verify failed: {chunk.hex()} != {expected.hex()}"
    print(f"  In-memory verification passed, new size = {fmt_bytes(buf.size)}")
    print()

    # 7. Save As
    print(f"Saving to {saved.name}...")
    t0 = time.perf_counter()
    buf.save(saved)
    save_time = time.perf_counter() - t0
    print(f"  Save completed in {save_time:.3f}s")
    print()

    buf.close()

    # 8. Reopen saved file and verify
    print(f"Reopening saved file and verifying...")
    t0 = time.perf_counter()
    saved_buf = Buffer.open(saved)
    reopen_time = time.perf_counter() - t0
    print(f"  Reopened in {reopen_time:.3f}s, size = {fmt_bytes(saved_buf.size)}")
    assert saved_buf.size == expected_final_size

    checks = [
        (replace_offset - 4, 12, b"\x00\x00\x00\x3F" + replace_new + b"\x00\x00\x00\x41"),
        (insert_offset - 4, 12, b"\x00\x00\x00\x7F" + insert_data + b"\x00\x00\x00\x80"),
        (large_offset - 4, 20, b"\x00\x00\x00\xBF" + large_new + b"\x00\x00\x00\xC2"),
    ]
    for off, length, expected in checks:
        chunk = saved_buf.read(off, length)
        assert chunk == expected, f"saved verify failed at 0x{off:x}: {chunk.hex()} != {expected.hex()}"
    print("  Saved-file verification passed")
    print()

    saved_buf.close()

    # Summary
    print("=" * 60)
    print("Benchmark summary")
    print("=" * 60)
    print(f"  Generate 1 GiB file      : {gen_time:.3f}s")
    print(f"  Open                     : {open_time:.3f}s")
    print(f"  Search (1 hit in 1 GiB)  : {search_time:.3f}s")
    print(f"  Replace (4 -> 4 bytes)   : {replace_time:.3f}s")
    print(f"  Insert (4 bytes)         : {insert_time:.3f}s")
    print(f"  Replace (8 -> 12 bytes)  : {large_replace_time:.3f}s")
    print(f"  Save As (1 GiB + 8 B)    : {save_time:.3f}s")
    print(f"  Reopen saved file        : {reopen_time:.3f}s")
    print(f"  Final saved size         : {fmt_bytes(expected_final_size)}")
    print()
    print("All correctness checks passed.")

    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Cleaned up temporary files in {tmp_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
