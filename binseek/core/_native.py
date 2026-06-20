"""ctypes binding for the binseek C++ core shared library."""

from __future__ import annotations

import ctypes
import platform
import sys
from pathlib import Path
from typing import Optional


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
    try:
        return ctypes.CDLL(str(lib_path))
    except OSError as exc:
        raise RuntimeError(f"Failed to load native core library: {exc}") from exc


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
