"""Hex view widget."""

from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, Optional, Set

from textual.widgets import Static
from textual.events import Key
from rich.text import Text

from binseek.model.buffer import Buffer
from binseek.ui.help_dialog import HelpDialog


class EditMode(Enum):
    VIEW = auto()
    REPLACE = auto()
    INSERT = auto()


class HexView(Static):
    """Page-based hex/ASCII viewer with keyboard navigation and editing."""

    can_focus = True

    DEFAULT_CSS = """
    HexView {
        height: 1fr;
        width: 100%;
        overflow: auto scroll;
        background: $surface-darken-1;
        color: $text;
        padding: 0 1;
        content-align: left top;
    }
    """

    BYTES_PER_ROW = 16
    PAGE_ROWS = 16

    def __init__(self, *args, **kwargs) -> None:
        super().__init__("", *args, **kwargs)
        self._buffer: Buffer | None = None
        self._offset = 0
        self._cursor = 0
        self._search_results: Set[int] = set()
        self._search_current: Optional[int] = None
        self._mode = EditMode.VIEW
        self._pending_nibble: Optional[int] = None

    @property
    def buffer(self) -> Buffer | None:
        return self._buffer

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def edit_mode(self) -> str:
        return self._mode.name

    @property
    def pending_str(self) -> str:
        if self._pending_nibble is None:
            return ""
        return f"{self._pending_nibble:X}"

    def set_buffer(self, buffer: Buffer | None) -> None:
        self._buffer = buffer
        self._offset = 0
        self._cursor = 0
        self._search_results.clear()
        self._search_current = None
        self._mode = EditMode.VIEW
        self._pending_nibble = None
        self.refresh_view()

    @property
    def page_size(self) -> int:
        return self.BYTES_PER_ROW * self.PAGE_ROWS

    def _ensure_visible(self) -> None:
        size = self._buffer.size if self._buffer else 0
        if size == 0:
            self._cursor = 0
            self._offset = 0
            return
        self._cursor = max(0, min(self._cursor, size - 1))
        page_start = (self._cursor // self.page_size) * self.page_size
        self._offset = max(0, min(page_start, size - 1))

    def jump_to(self, offset: int) -> None:
        if not self._buffer:
            return
        self._cursor = offset
        self._ensure_visible()
        self.refresh_view()

    def set_search_results(self, results: Iterable[int], current: Optional[int] = None) -> None:
        self._search_results = set(results)
        self._search_current = current
        self.refresh_view()

    def clear_search_results(self) -> None:
        self._search_results.clear()
        self._search_current = None
        self.refresh_view()

    def set_mode(self, mode: EditMode) -> None:
        self._mode = mode
        self._pending_nibble = None
        self.refresh_view()

    def _apply_byte(self, byte: int) -> None:
        if not self._buffer:
            return
        size = self._buffer.size
        if self._mode == EditMode.REPLACE:
            if self._cursor >= size:
                self.app.notify("Cannot replace beyond end of file", severity="warning")
                return
            self._buffer.replace(self._cursor, 1, bytes([byte]))
        elif self._mode == EditMode.INSERT:
            self._buffer.replace(self._cursor, 0, bytes([byte]))
        else:
            return
        self._cursor += 1
        self._ensure_visible()

    def _handle_hex_digit(self, char: str) -> None:
        value = int(char, 16)
        if self._pending_nibble is None:
            self._pending_nibble = value
        else:
            byte = (self._pending_nibble << 4) | value
            self._pending_nibble = None
            self._apply_byte(byte)
        self.refresh_view()

    def refresh_view(self) -> None:
        if not self._buffer:
            self.update("No file open")
            return

        size = self._buffer.size
        if size == 0:
            self.update("Empty file")
            return

        data = self._buffer.read(self._offset, min(self.page_size, size - self._offset))
        text = Text()
        for row in range(self.PAGE_ROWS):
            row_offset = self._offset + row * self.BYTES_PER_ROW
            if row_offset >= size:
                break
            row_data = data[row * self.BYTES_PER_ROW : (row + 1) * self.BYTES_PER_ROW]
            line = Text()
            line.append(f"{row_offset:08X}  ", style="bold cyan")

            hex_parts = []
            ascii_chars = []
            for col, byte in enumerate(row_data):
                abs_offset = row_offset + col
                style = ""
                if abs_offset == self._cursor:
                    if self._mode == EditMode.REPLACE:
                        style = "bold black on red"
                    elif self._mode == EditMode.INSERT:
                        style = "bold black on green"
                    else:
                        style = "reverse"
                elif abs_offset == self._search_current:
                    style = "bold magenta on yellow"
                elif abs_offset in self._search_results:
                    style = "bold yellow"
                hex_parts.append((f"{byte:02X} ", style))
                ch = chr(byte) if 32 <= byte < 127 else "."
                ascii_chars.append((ch, style))

            for part, style in hex_parts:
                line.append(part, style=style)
            missing = self.BYTES_PER_ROW - len(row_data)
            line.append("   " * missing)
            line.append(" |")
            for ch, style in ascii_chars:
                line.append(ch, style=style)
            line.append("|")
            text.append(line)
            if row + 1 < self.PAGE_ROWS and row_offset + self.BYTES_PER_ROW < size:
                text.append("\n")
        self.update(text)
        self.app.refresh_status()

    def move_cursor(self, delta: int) -> None:
        if not self._buffer:
            return
        self._cursor += delta
        self._ensure_visible()
        self.refresh_view()

    def on_key(self, event: Key) -> None:
        if not self._buffer:
            return

        # Editing input (only active in REPLACE / INSERT modes).
        if (
            len(event.key) == 1
            and event.key in "0123456789abcdefABCDEF"
            and self._mode in (EditMode.REPLACE, EditMode.INSERT)
        ):
            self._handle_hex_digit(event.key)
            event.stop()
            return

        bpr = self.BYTES_PER_ROW
        if event.key == "left":
            self.move_cursor(-1)
        elif event.key == "right":
            self.move_cursor(1)
        elif event.key == "up":
            self.move_cursor(-bpr)
        elif event.key == "down":
            self.move_cursor(bpr)
        elif event.key == "pageup":
            self.move_cursor(-self.page_size)
        elif event.key == "pagedown":
            self.move_cursor(self.page_size)
        elif event.key == "home":
            self._cursor = 0
            self._ensure_visible()
            self.refresh_view()
        elif event.key == "end":
            self._cursor = max(0, self._buffer.size - 1)
            self._ensure_visible()
            self.refresh_view()
        elif event.key == "e":
            if self._mode == EditMode.REPLACE:
                self.set_mode(EditMode.VIEW)
            else:
                self.set_mode(EditMode.REPLACE)
        elif event.key == "insert":
            if self._mode == EditMode.INSERT:
                self.set_mode(EditMode.VIEW)
            else:
                self.set_mode(EditMode.INSERT)
        elif event.key == "escape":
            self.set_mode(EditMode.VIEW)
        elif event.key == "h" and self._mode == EditMode.VIEW:
            self.app.push_screen(HelpDialog())
            return
        else:
            return
        event.stop()
