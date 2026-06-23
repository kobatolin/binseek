"""ctypes binding for the binseek C++ core shared library."""

from __future__ import annotations

import ctypes
import os
import platform
import sys
from pathlib import Path
from typing import List, Optional, Tuple


class _BsMatch(ctypes.Structure):
    _fields_ = [("offset", ctypes.c_uint64), ("length", ctypes.c_uint64)]


def _library_path() -> Path:
    """Locate libcore.{so,dll} in the binseek package root."""
    here = Path(__file__).resolve().parent.parent
    system = platform.system()
    if system == "Windows":
        name = "libcore.dll"
    elif system == "Linux":
        name = "libcore.so"
    elif system == "Darwin":
        name = "libcore.dylib"
    else:
        # Best effort for other POSIX systems.
        name = "libcore.so"
    return here / name


def _load_library() -> ctypes.CDLL:
    lib_path = _library_path()
    if not lib_path.exists():
        raise RuntimeError(
            f"Native core library not found: {lib_path}\n"
            "Run 'make linux' or 'make windows' first."
        )
    here = lib_path.parent
    dll_dir = None
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        # Ensure dependent DLLs (libboost_regex.dll) in the same package dir are found.
        dll_dir = os.add_dll_directory(str(here))
    try:
        return ctypes.CDLL(str(lib_path))
    except OSError as exc:
        raise RuntimeError(f"Failed to load native core library: {exc}") from exc
    finally:
        if dll_dir is not None:
            dll_dir.close()


_lib = _load_library()

_lib.bs_open.argtypes = [ctypes.c_char_p]
_lib.bs_open.restype = ctypes.c_void_p

_lib.bs_close.argtypes = [ctypes.c_void_p]
_lib.bs_close.restype = None

_lib.bs_get_error.argtypes = [ctypes.c_void_p]
_lib.bs_get_error.restype = ctypes.c_char_p

_lib.bs_get_size.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint64)]
_lib.bs_get_size.restype = ctypes.c_int

_lib.bs_read_chunk.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_uint64,
    ctypes.POINTER(ctypes.c_uint8),
]
_lib.bs_read_chunk.restype = ctypes.c_int

_lib.bs_search.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_uint64,
    ctypes.c_uint64,
    ctypes.c_uint64,
    ctypes.c_int,
    ctypes.POINTER(_BsMatch),
    ctypes.POINTER(ctypes.c_uint64),
]
_lib.bs_search.restype = ctypes.c_int

_lib.bs_search_regex.argtypes = [
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.c_uint64,
    ctypes.c_uint64,
    ctypes.c_int,
    ctypes.POINTER(_BsMatch),
    ctypes.POINTER(ctypes.c_uint64),
]
_lib.bs_search_regex.restype = ctypes.c_int

_lib.bs_replace.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_uint64,
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_uint64,
]
_lib.bs_replace.restype = ctypes.c_int

_lib.bs_save.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.bs_save.restype = ctypes.c_int


class CoreError(Exception):
    """Error returned by the native core."""

    pass


class Core:
    """Wrapper around the binseek native core handle."""

    def __init__(self, handle: int) -> None:
        self._handle = ctypes.c_void_p(handle)

    def _check(self, rc: int) -> None:
        if rc != 0:
            msg = self.error or "native core error"
            raise CoreError(msg)

    @property
    def error(self) -> Optional[str]:
        raw = _lib.bs_get_error(self._handle)
        if raw:
            return raw.decode("utf-8", errors="replace")
        return None

    @classmethod
    def open(cls, path: str | Path) -> "Core":
        handle = _lib.bs_open(str(path).encode("utf-8"))
        if not handle:
            raw = _lib.bs_get_error(None)
            msg = raw.decode("utf-8", errors="replace") if raw else "failed to open file"
            raise CoreError(msg)
        return cls(handle)

    def close(self) -> None:
        if self._handle:
            _lib.bs_close(self._handle)
            self._handle = ctypes.c_void_p(0)

    def __enter__(self) -> "Core":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def size(self) -> int:
        size = ctypes.c_uint64(0)
        self._check(_lib.bs_get_size(self._handle, ctypes.byref(size)))
        return size.value

    def read_chunk(self, offset: int, length: int) -> bytes:
        if length < 0:
            raise ValueError("length must be non-negative")
        if length == 0:
            return b""
        buf = (ctypes.c_uint8 * length)()
        self._check(_lib.bs_read_chunk(self._handle, offset, length, buf))
        return bytes(buf)

    def search(
        self,
        pattern: bytes,
        start: int = 0,
        max_results: int = 1000,
        case_insensitive: bool = False,
    ) -> List[Tuple[int, int]]:
        if not pattern:
            return []
        if max_results <= 0:
            return []
        pattern_len = len(pattern)
        pat_buf = (ctypes.c_uint8 * pattern_len).from_buffer_copy(pattern)
        results = (_BsMatch * max_results)()
        count = ctypes.c_uint64(0)
        self._check(
            _lib.bs_search(
                self._handle,
                pat_buf,
                pattern_len,
                start,
                max_results,
                1 if case_insensitive else 0,
                results,
                ctypes.byref(count),
            )
        )
        return [(results[i].offset, results[i].length) for i in range(count.value)]

    def search_regex(
        self,
        pattern: str,
        start: int = 0,
        max_results: int = 1000,
        hex_mode: bool = False,
        case_insensitive: bool = False,
    ) -> List[Tuple[int, int]]:
        if not pattern:
            return []
        if max_results <= 0:
            return []
        results = (_BsMatch * max_results)()
        count = ctypes.c_uint64(0)
        flags = 0
        if hex_mode:
            flags |= 0x01
        if case_insensitive:
            flags |= 0x02
        self._check(
            _lib.bs_search_regex(
                self._handle,
                pattern.encode("utf-8"),
                start,
                max_results,
                flags,
                results,
                ctypes.byref(count),
            )
        )
        return [(results[i].offset, results[i].length) for i in range(count.value)]

    def replace(self, offset: int, old_len: int, new_data: bytes) -> None:
        new_len = len(new_data)
        if new_len == 0:
            new_buf = None
        else:
            new_buf = (ctypes.c_uint8 * new_len).from_buffer_copy(new_data)
        self._check(
            _lib.bs_replace(
                self._handle,
                offset,
                old_len,
                new_buf,
                new_len,
            )
        )

    def save(self, out_path: str | Path) -> None:
        self._check(_lib.bs_save(self._handle, str(out_path).encode("utf-8")))
