"""High-level buffer model wrapping the native core."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from binseek.core._native import Core, CoreError


class Buffer:
    """Editable binary buffer backed by the C++ core."""

    def __init__(self, core: Core, path: str | Path) -> None:
        self._core = core
        self._path = Path(path)
        self._dirty = False
        self._search_results: List[int] = []
        self._search_index = -1
        self._last_pattern: Optional[bytes] = None

    @classmethod
    def open(cls, path: str | Path) -> "Buffer":
        core = Core.open(path)
        return cls(core, path)

    def close(self) -> None:
        self._core.close()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def size(self) -> int:
        return self._core.size()

    def read(self, offset: int, length: int) -> bytes:
        return self._core.read_chunk(offset, length)

    def search(self, pattern: bytes, start: int = 0, max_results: int = 1000) -> List[int]:
        self._last_pattern = pattern
        self._search_results = self._core.search(pattern, start=start, max_results=max_results)
        self._search_index = 0 if self._search_results else -1
        return self._search_results

    def search_next(self) -> Optional[int]:
        if not self._search_results:
            return None
        self._search_index = (self._search_index + 1) % len(self._search_results)
        return self._search_results[self._search_index]

    def search_prev(self) -> Optional[int]:
        if not self._search_results:
            return None
        self._search_index = (self._search_index - 1) % len(self._search_results)
        return self._search_results[self._search_index]

    def current_search_result(self) -> Optional[int]:
        if 0 <= self._search_index < len(self._search_results):
            return self._search_results[self._search_index]
        return None

    def replace(self, offset: int, old_len: int, new_data: bytes) -> None:
        self._core.replace(offset, old_len, new_data)
        self._dirty = True

    def save(self, out_path: Optional[str | Path] = None) -> None:
        target = Path(out_path) if out_path else self._path
        self._core.save(target)
        self._path = target
        self._dirty = False
