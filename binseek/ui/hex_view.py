"""Hex view widget."""

from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, Optional, Set

from textual.widgets import Static
from textual.events import Key
from rich.text import Text

from binseek.model.buffer import Buffer
from binseek.ui.help_dialog import HELP_TEXT


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
        overflow: hidden;
        background: $surface-darken-1;
        color: $text;
        padding: 0 1;
        content-align: left top;
    }
    """

    BYTES_PER_ROW = 16

    def __init__(self, *args, **kwargs) -> None:
        super().__init__("", *args, **kwargs)
        self._buffer: Buffer | None = None
        self._offset = 0
        self._cursor = 0
        self._search_results: Set[int] = set()
        self._search_current: Optional[int] = None
        self._mode = EditMode.VIEW
        self._pending_nibble: Optional[int] = None
        self._page_rows = 16

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
    def page_rows(self) -> int:
        return self._page_rows

    @property
    def page_size(self) -> int:
        return self.BYTES_PER_ROW * self._page_rows

    def _ensure_visible(self) -> None:
        size = self._buffer.size if self._buffer else 0
        if size == 0:
            self._cursor = 0
            self._offset = 0
            return

        # INSERT mode allows the cursor to sit one byte past the end so
        # bytes can be appended; other modes stay within [0, size-1].
        max_cursor = size if self._mode == EditMode.INSERT else size - 1
        self._cursor = max(0, min(self._cursor, max_cursor))

        page_size = self.page_size
        if size <= page_size:
            self._offset = 0
            return

        bpr = self.BYTES_PER_ROW
        # When the cursor is at the very end, align to the last full row.
        clamped = min(self._cursor, size - 1)
        row_start = (clamped // bpr) * bpr
        if row_start < self._offset:
            self._offset = row_start
        elif row_start + bpr > self._offset + page_size:
            new_offset = row_start + bpr - page_size
            max_offset = size - page_size
            self._offset = min(new_offset, max_offset)
        # else: cursor already visible, keep current offset

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
        self._ensure_visible()
        self.refresh_view()

    def on_resize(self) -> None:
        new_rows = max(1, self.size.height)
        if new_rows != self._page_rows:
            self._page_rows = new_rows
            self._ensure_visible()
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
            message = Text()
            message.append("No file open\n\n", style="bold")
            message.append(HELP_TEXT)
            self.update(message)
            return

        size = self._buffer.size
        if size == 0:
            self.update("Empty file")
            return

        data = self._buffer.read(self._offset, min(self.page_size, size - self._offset))
        text = Text()
        for row in range(self._page_rows):
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
            if row + 1 < self._page_rows and row_offset + self.BYTES_PER_ROW < size:
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
        if event.key in ("left", "h"):
            self.move_cursor(-1)
        elif event.key in ("right", "l"):
            self.move_cursor(1)
        elif event.key in ("up", "k"):
            self.move_cursor(-bpr)
        elif event.key in ("down", "j"):
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
            max_cursor = self._buffer.size if self._mode == EditMode.INSERT else self._buffer.size - 1
            self._cursor = max(0, max_cursor)
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
        else:
            return
        event.stop()
