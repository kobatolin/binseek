"""Hex view widget."""

from __future__ import annotations

import struct
from enum import Enum, auto
from typing import Iterable, List, Optional, Set, Tuple

from textual.widgets import Static
from textual.events import Key, MouseScrollDown, MouseScrollUp, MouseUp
from rich.text import Text

from binseek.model.buffer import Buffer
from binseek.ui.help_dialog import HELP_TEXT


class EditMode(Enum):
    VIEW = auto()
    REPLACE = auto()
    INSERT = auto()


class EditWorkspace(Enum):
    HEX = auto()
    ASCII = auto()


class DisplayMode(Enum):
    BYTE = 1
    WORD = 2
    DWORD = 4


class Endian(Enum):
    LITTLE = "little"
    BIG = "big"


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
        self._workspace = EditWorkspace.HEX
        self._pending_value = 0
        self._pending_nibbles = 0
        self._page_rows = 16
        self._display_mode = DisplayMode.BYTE
        self._endian = Endian.LITTLE

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
    def workspace(self) -> str:
        return self._workspace.name

    @property
    def display_mode(self) -> str:
        return f"{self._display_mode.value}B"

    @property
    def endian(self) -> str:
        return "BE" if self._endian == Endian.BIG else "LE"

    @property
    def pending_str(self) -> str:
        if self._pending_nibbles == 0:
            return ""
        return f"{self._pending_value:0{self._pending_nibbles}X}"

    def set_buffer(self, buffer: Buffer | None) -> None:
        self._buffer = buffer
        self._offset = 0
        self._cursor = 0
        self._search_results.clear()
        self._search_current = None
        self._mode = EditMode.VIEW
        self._workspace = EditWorkspace.HEX
        self._pending_value = 0
        self._pending_nibbles = 0
        self._display_mode = DisplayMode.BYTE
        self._endian = Endian.LITTLE
        self.refresh_view()

    @property
    def _group_size(self) -> int:
        return self._display_mode.value

    @property
    def _struct_fmt(self) -> str:
        endian_char = ">" if self._endian == Endian.BIG else "<"
        if self._group_size == 2:
            return f"{endian_char}H"
        return f"{endian_char}I"

    @property
    def page_rows(self) -> int:
        return self._page_rows

    @property
    def page_size(self) -> int:
        return self.BYTES_PER_ROW * self._page_rows

    def _align_cursor(self) -> None:
        gs = self._group_size
        self._cursor = (self._cursor // gs) * gs

    def _max_cursor(self) -> int:
        size = self._buffer.size if self._buffer else 0
        gs = self._group_size
        if size == 0:
            return 0
        if self._mode == EditMode.INSERT:
            return size if size % gs == 0 else (size // gs) * gs
        return ((size - 1) // gs) * gs

    def _ensure_visible(self) -> None:
        if not self._buffer:
            self._cursor = 0
            self._offset = 0
            return

        size = self._buffer.size
        if size == 0:
            self._cursor = 0
            self._offset = 0
            return

        self._cursor = max(0, min(self._cursor, self._max_cursor()))

        page_size = self.page_size
        if size <= page_size:
            self._offset = 0
            return

        bpr = self.BYTES_PER_ROW
        clamped = min(self._cursor, size - 1)
        row_start = (clamped // bpr) * bpr
        if row_start < self._offset:
            self._offset = row_start
        elif row_start + bpr > self._offset + page_size:
            # Scroll down just enough to bring the cursor row into view,
            # but never past the last aligned page.
            new_offset = row_start + bpr - page_size
            new_offset = (new_offset // bpr) * bpr
            last_row_start = ((size - 1) // bpr) * bpr
            max_offset = max(0, last_row_start - (self._page_rows - 1) * bpr)
            self._offset = min(new_offset, max_offset)

    def jump_to(self, offset: int) -> None:
        if not self._buffer:
            return
        self._cursor = offset
        self._align_cursor()
        self._ensure_visible()
        self.refresh_view()

    def set_search_results(
        self, results: Iterable[Tuple[int, int]], current: Optional[int] = None
    ) -> None:
        self._search_results = set()
        for start, length in results:
            self._search_results.update(range(start, start + length))
        self._search_current = current
        self.refresh_view()

    def clear_search_results(self) -> None:
        self._search_results.clear()
        self._search_current = None
        self.refresh_view()

    def set_mode(self, mode: EditMode) -> None:
        self._mode = mode
        if self._mode == EditMode.VIEW:
            self._workspace = EditWorkspace.HEX
        self._pending_value = 0
        self._pending_nibbles = 0
        self._align_cursor()
        self._ensure_visible()
        self.refresh_view()

    def set_workspace(self, workspace: EditWorkspace) -> None:
        self._workspace = workspace
        if self._workspace == EditWorkspace.ASCII and self._display_mode != DisplayMode.BYTE:
            self._display_mode = DisplayMode.BYTE
        self._pending_value = 0
        self._pending_nibbles = 0
        self._align_cursor()
        self._ensure_visible()
        self.refresh_view()

    def toggle_workspace(self) -> None:
        new_workspace = EditWorkspace.ASCII if self._workspace == EditWorkspace.HEX else EditWorkspace.HEX
        self.set_workspace(new_workspace)

    def set_display_mode(self, mode: DisplayMode) -> None:
        if self._workspace == EditWorkspace.ASCII and mode != DisplayMode.BYTE:
            self._workspace = EditWorkspace.HEX
        self._display_mode = mode
        self._pending_value = 0
        self._pending_nibbles = 0
        self._align_cursor()
        self._ensure_visible()
        self.refresh_view()

    def on_resize(self) -> None:
        new_rows = max(1, self.size.height)
        if new_rows != self._page_rows:
            self._page_rows = new_rows
            self._ensure_visible()
            self.refresh_view()

    def _pack_value(self, value: int) -> bytes:
        if self._group_size == 1:
            return bytes([value])
        return struct.pack(self._struct_fmt, value)

    def _apply_value(self, value: int) -> None:
        if not self._buffer:
            return
        size = self._buffer.size
        gs = self._group_size
        packed = self._pack_value(value)
        if self._mode == EditMode.REPLACE:
            if self._cursor + gs > size:
                self.app.notify("Cannot replace beyond end of file", severity="warning")
                return
            self._buffer.replace(self._cursor, gs, packed)
        elif self._mode == EditMode.INSERT:
            self._buffer.replace(self._cursor, 0, packed)
        else:
            return
        self._cursor += gs
        self._ensure_visible()

    def _handle_hex_digit(self, char: str) -> None:
        value = int(char, 16)
        self._pending_value = (self._pending_value << 4) | value
        self._pending_nibbles += 1
        required = self._group_size * 2
        if self._pending_nibbles >= required:
            self._apply_value(self._pending_value)
            self._pending_value = 0
            self._pending_nibbles = 0
        self.refresh_view()

    def _handle_ascii_char(self, char: str) -> None:
        code = ord(char)
        if not (32 <= code < 127):
            return
        self._apply_value(code)
        self.refresh_view()

    def _style_for_offset(self, offset: int) -> str:
        if offset == self._cursor:
            if self._workspace == EditWorkspace.ASCII:
                if self._mode == EditMode.REPLACE:
                    return "bold black on blue"
                if self._mode == EditMode.INSERT:
                    return "bold black on cyan"
                return "reverse underline"
            if self._mode == EditMode.REPLACE:
                return "bold black on red"
            if self._mode == EditMode.INSERT:
                return "bold black on green"
            return "reverse"
        if offset == self._search_current:
            return "bold magenta on yellow"
        if offset in self._search_results:
            return "bold yellow"
        return ""

    def refresh_view(self) -> None:
        if not self._buffer:
            message = Text()
            message.append("No file open\n\n", style="bold")
            message.append(HELP_TEXT)
            self.update(message)
            return

        size = self._buffer.size
        append_cursor = self._mode == EditMode.INSERT and self._cursor == size
        placeholder_style = "bold black on green"
        group_size = self._group_size
        hex_width = (group_size * 2 + 1) * (self.BYTES_PER_ROW // group_size)

        if size == 0:
            if not append_cursor:
                self.update("Empty file")
                return
            text = Text()
            line = Text()
            line.append("00000000  ", style="bold cyan")
            placeholder = "_" * (group_size * 2) + " "
            line.append(placeholder, style=placeholder_style)
            line.append(" " * (hex_width - len(placeholder)))
            line.append(" |")
            line.append(" " * group_size, style=placeholder_style)
            line.append(" " * (self.BYTES_PER_ROW - group_size))
            line.append("|")
            text.append(line)
            self.update(text)
            self.app.refresh_status()
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
            col = 0
            while col < len(row_data):
                if group_size > 1 and col + group_size <= len(row_data):
                    chunk = row_data[col : col + group_size]
                    value = struct.unpack(self._struct_fmt, bytes(chunk))[0]
                    hex_digits = f"{value:0{group_size * 2}X}"
                    base = row_offset + col
                    byte_styles = [self._style_for_offset(base + i) for i in range(group_size)]
                    group_style = ""
                    for i in range(group_size):
                        if base + i == self._cursor:
                            group_style = byte_styles[i]
                            break
                    if group_style:
                        hex_parts.append((hex_digits + " ", group_style))
                        for b in chunk:
                            ascii_chars.append((chr(b) if 32 <= b < 127 else ".", group_style))
                    else:
                        pairs = [hex_digits[i : i + 2] for i in range(0, len(hex_digits), 2)]
                        for i, pair in enumerate(pairs):
                            byte_index = i if self._endian == Endian.BIG else group_size - 1 - i
                            hex_parts.append((pair, byte_styles[byte_index]))
                        trailing_space_style = byte_styles[-1] if self._endian == Endian.BIG else byte_styles[0]
                        hex_parts.append((" ", trailing_space_style))
                        for i, b in enumerate(chunk):
                            ascii_chars.append((chr(b) if 32 <= b < 127 else ".", byte_styles[i]))
                    col += group_size
                else:
                    byte = row_data[col]
                    style = self._style_for_offset(row_offset + col)
                    hex_parts.append((f"{byte:02X} ", style))
                    ascii_chars.append((chr(byte) if 32 <= byte < 127 else ".", style))
                    col += 1

            row_end = row_offset + len(row_data)
            if append_cursor and row_end == size:
                placeholder = "_" * (group_size * 2) + " "
                hex_parts.append((placeholder, placeholder_style))
                ascii_chars.append((" " * group_size, placeholder_style))

            rendered_width = sum(len(part) for part, _ in hex_parts)
            for part, style in hex_parts:
                line.append(part, style=style)
            line.append(" " * max(0, hex_width - rendered_width))

            line.append(" |")
            for ch, style in ascii_chars:
                line.append(ch, style=style)
            line.append("|")
            text.append(line)
            if row + 1 < self._page_rows and row_offset + self.BYTES_PER_ROW < size:
                text.append("\n")

        if append_cursor and size % self.BYTES_PER_ROW == 0 and self._offset <= size < self._offset + self.page_size:
            if text:
                text.append("\n")
            line = Text()
            line.append(f"{size:08X}  ", style="bold cyan")
            placeholder = "_" * (group_size * 2) + " "
            line.append(placeholder, style=placeholder_style)
            line.append(" " * (hex_width - len(placeholder)))
            line.append(" |")
            line.append(" " * group_size, style=placeholder_style)
            line.append(" " * (self.BYTES_PER_ROW - group_size))
            line.append("|")
            text.append(line)

        self.update(text)
        self.app.refresh_status()

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:
        if not self._buffer:
            return
        self.move_cursor(-self.BYTES_PER_ROW * 3)
        event.stop()

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:
        if not self._buffer:
            return
        self.move_cursor(self.BYTES_PER_ROW * 3)
        event.stop()

    def _offset_from_mouse(self, x: int, y: int) -> Optional[int]:
        if not self._buffer:
            return None
        size = self._buffer.size
        if size == 0:
            return None
        row_offset = self._offset + y * self.BYTES_PER_ROW
        if row_offset >= size:
            return None
        group_size = self._group_size
        hex_width = (group_size * 2 + 1) * (self.BYTES_PER_ROW // group_size)
        addr_width = 10
        ascii_start = addr_width + hex_width + 2

        if x < addr_width:
            return row_offset

        if x < addr_width + hex_width:
            if group_size == 1:
                col = (x - addr_width) // 3
            else:
                slot = x - addr_width
                slot_width = group_size * 2 + 1
                group_index = slot // slot_width
                within = slot % slot_width
                if within >= group_size * 2:
                    within = group_size * 2 - 1
                col = group_index * group_size + (within // 2)
            col = max(0, min(col, self.BYTES_PER_ROW - 1))
            offset = row_offset + col
            if offset >= size:
                return None
            if group_size > 1:
                offset = (offset // group_size) * group_size
            return offset

        if x < ascii_start:
            return row_offset

        col = x - ascii_start
        col = max(0, min(col, self.BYTES_PER_ROW - 1))
        offset = row_offset + col
        if offset >= size:
            return None
        return offset

    def on_mouse_up(self, event: MouseUp) -> None:
        if not self._buffer:
            return
        offset = self._offset_from_mouse(event.x, event.y)
        if offset is None:
            return
        self._cursor = offset
        self._align_cursor()
        self._ensure_visible()
        self.refresh_view()
        event.stop()

    def move_cursor(self, delta: int) -> None:
        if not self._buffer:
            return
        self._cursor += delta
        self._ensure_visible()
        self.refresh_view()

    def on_key(self, event: Key) -> None:
        if not self._buffer:
            return

        if (
            len(event.key) == 1
            and event.key in "0123456789abcdefABCDEF"
            and self._mode in (EditMode.REPLACE, EditMode.INSERT)
            and self._workspace == EditWorkspace.HEX
        ):
            self._handle_hex_digit(event.key)
            event.stop()
            return

        if (
            len(event.key) == 1
            and self._workspace == EditWorkspace.ASCII
            and self._mode in (EditMode.REPLACE, EditMode.INSERT)
        ):
            self._handle_ascii_char(event.key)
            event.stop()
            return

        gs = self._group_size
        bpr = self.BYTES_PER_ROW
        if event.key in ("left", "h"):
            self.move_cursor(-gs)
        elif event.key in ("right", "l"):
            self.move_cursor(gs)
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
            self._cursor = self._max_cursor()
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
        elif event.key == "delete":
            if self._mode != EditMode.INSERT or self._cursor >= self._buffer.size:
                return
            self._buffer.replace(self._cursor, 1, b"")
            self._pending_value = 0
            self._pending_nibbles = 0
            self._ensure_visible()
            self.refresh_view()
        elif event.key == "escape":
            self.set_mode(EditMode.VIEW)
        elif event.key == "tab":
            if self._mode in (EditMode.REPLACE, EditMode.INSERT):
                self.toggle_workspace()
            else:
                return
        elif event.key == "1":
            self.set_display_mode(DisplayMode.BYTE)
        elif event.key == "2":
            self.set_display_mode(DisplayMode.WORD)
        elif event.key == "4":
            self.set_display_mode(DisplayMode.DWORD)
        elif event.key == "b":
            self._endian = Endian.BIG if self._endian == Endian.LITTLE else Endian.LITTLE
            self.refresh_view()
        else:
            return
        event.stop()
