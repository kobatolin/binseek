"""Status bar widget."""

from __future__ import annotations

from textual.widgets import Static
from rich.text import Text


class StatusBar(Static):
    """Displays mode, file path, size, cursor offset and dirty state."""

    _last_args: dict | None = None

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $primary;
        color: $text;
        padding: 0 1;
        content-align: left middle;
    }
    """

    def update_status(
        self,
        mode: str = "VIEW",
        path: str = "",
        size: int = 0,
        offset: int = 0,
        dirty: bool = False,
        pending: str = "",
        display_mode: str = "1B",
        endian: str = "LE",
        workspace: str = "HEX",
        message: str = "",
    ) -> None:
        self._last_args = {
            "mode": mode,
            "path": path,
            "size": size,
            "offset": offset,
            "dirty": dirty,
            "pending": pending,
            "display_mode": display_mode,
            "endian": endian,
            "workspace": workspace,
            "message": message,
        }
        if message:
            self.update(Text(message))
            return
        dirty_mark = " *" if dirty else ""
        left_prefix = f"[{mode} {display_mode} {endian} {workspace}] "
        path_part = f"{path}{dirty_mark}"
        right = f" | Size: {size} | Offset: 0x{offset:08X} ({offset})"
        if pending:
            right += f" | Pending: {pending}"
        text = self._fit_status(left_prefix, path_part, right)
        self.update(Text(text))

    def on_resize(self) -> None:
        if self._last_args is not None:
            self.update_status(**self._last_args)

    def _fit_status(self, left_prefix: str, path_part: str, right: str) -> str:
        width = self.size.width
        if not width:
            return left_prefix + path_part + right
        content_width = width - 2
        left = left_prefix + path_part
        if len(left) + len(right) <= content_width:
            return left + right
        available = content_width - len(right)
        if available <= 0:
            return left_prefix + path_part + right
        if len(left) <= available:
            return left + right
        if available <= len(left_prefix):
            return self._ellipsize(left, available) + right
        path_available = available - len(left_prefix)
        if path_available <= 0:
            return left_prefix + right
        path_part = self._ellipsize(path_part, path_available)
        return left_prefix + path_part + right

    @staticmethod
    def _ellipsize(text: str, max_width: int) -> str:
        if max_width <= 0:
            return ""
        if len(text) <= max_width:
            return text
        if max_width <= 3:
            return "..."[:max_width]
        head = (max_width - 3) // 2
        tail = max_width - 3 - head
        return text[:head] + "..." + text[-tail:]
