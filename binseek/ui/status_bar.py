"""Status bar widget."""

from __future__ import annotations

from textual.widgets import Static
from rich.text import Text


class StatusBar(Static):
    """Displays mode, file path, size, cursor offset and dirty state."""

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
        if message:
            self.update(Text(message))
            return
        dirty_mark = " *" if dirty else ""
        text = f"[{mode} {display_mode} {endian} {workspace}] {path}{dirty_mark} | Size: {size} | Offset: 0x{offset:08X} ({offset})"
        if pending:
            text += f" | Pending: {pending}"
        self.update(Text(text))
