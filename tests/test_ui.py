"""Tests for the Textual UI widgets."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from textual.app import App
from textual.containers import VerticalScroll
from textual.widgets import Button, Static

from binseek import __version__
from binseek.app import BinseekApp
from binseek.ui.confirm_dialog import ConfirmDialog
from binseek.ui.file_dialog import FileDialog
from binseek.ui.help_dialog import HELP_TEXT, HelpDialog


def test_hex_view_shows_welcome_when_no_file_open() -> None:
    async def _run() -> None:
        app = BinseekApp()
        async with app.run_test() as pilot:
            hex_view = app.query_one("#hex")
            content = str(hex_view._Static__content)
            assert "BINSEEK" in content
            assert __version__ in content
            assert "Press F1 for Help" in content
            assert "Press F2 to Open File" in content

    asyncio.run(_run())


def test_hjkl_navigates_when_file_open() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"A" * 256)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            assert hex_view.cursor == 0
            await pilot.press("l")
            assert hex_view.cursor == 1
            await pilot.press("j")
            assert hex_view.cursor == 1 + hex_view.BYTES_PER_ROW
            await pilot.press("h")
            assert hex_view.cursor == hex_view.BYTES_PER_ROW
            await pilot.press("k")
            assert hex_view.cursor == 0

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_find_highlights_full_match_range() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"xxABCxxABCxx")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            results = app._buffer.search(b"ABC")
            assert results == [(2, 3), (7, 3)]
            hex_view.set_search_results(results, results[0][0])
            assert hex_view._search_current == 2
            assert hex_view._search_results == {2, 3, 4, 7, 8, 9}

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_confirm_dialog_keyboard_navigation() -> None:
    """Confirm dialog buttons can be switched with arrow keys and Tab."""

    async def _run() -> None:
        app = App()
        async with app.run_test() as pilot:
            app.push_screen(
                ConfirmDialog(
                    "Save changes?",
                    save_text="Save",
                    discard_text="Discard",
                )
            )
            await pilot.pause()
            buttons = list(app.screen.query(Button))
            assert len(buttons) == 3
            assert app.screen.focused is buttons[0]

            await pilot.press("right")
            await pilot.pause()
            assert app.screen.focused is buttons[1]

            await pilot.press("right")
            await pilot.pause()
            assert app.screen.focused is buttons[2]

            await pilot.press("left")
            await pilot.pause()
            assert app.screen.focused is buttons[1]

            await pilot.press("tab")
            await pilot.pause()
            assert app.screen.focused is buttons[2]

            await pilot.press("shift+tab")
            await pilot.pause()
            assert app.screen.focused is buttons[1]

    asyncio.run(_run())


def test_mouse_wheel_scrolls_by_three_rows() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"A" * 256)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            assert hex_view.cursor == 0

            from textual.events import MouseScrollDown, MouseScrollUp

            hex_view.on_mouse_scroll_down(
                MouseScrollDown(hex_view, 0, 0, 0, 0, 0, False, False, False)
            )
            await pilot.pause()
            assert hex_view.cursor == hex_view.BYTES_PER_ROW * 3

            hex_view.on_mouse_scroll_up(
                MouseScrollUp(hex_view, 0, 0, 0, 0, 0, False, False, False)
            )
            await pilot.pause()
            assert hex_view.cursor == 0

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_mouse_click_selects_byte_in_hex_area() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")

            from textual.events import MouseUp

            # Row 0 address width = 10, first hex byte "41" at x=10..11, space at x=12
            hex_view.on_mouse_up(MouseUp(hex_view, 10, 0, 0, 0, 1, False, False, False))
            await pilot.pause()
            assert hex_view.cursor == 0

            hex_view.on_mouse_up(MouseUp(hex_view, 13, 0, 0, 0, 1, False, False, False))
            await pilot.pause()
            assert hex_view.cursor == 1

            hex_view.on_mouse_up(MouseUp(hex_view, 22, 0, 0, 0, 1, False, False, False))
            await pilot.pause()
            assert hex_view.cursor == 4

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_mouse_click_selects_byte_in_ascii_area() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            hex_width = (1 * 2 + 1) * hex_view.BYTES_PER_ROW
            ascii_start = 10 + hex_width + 2

            from textual.events import MouseUp

            hex_view.on_mouse_up(
                MouseUp(hex_view, ascii_start, 0, 0, 0, 1, False, False, False)
            )
            await pilot.pause()
            assert hex_view.cursor == 0

            hex_view.on_mouse_up(
                MouseUp(hex_view, ascii_start + 2, 0, 0, 0, 1, False, False, False)
            )
            await pilot.pause()
            assert hex_view.cursor == 2

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_mouse_click_selects_group_in_word_mode() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"\x00" * 16)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("2")
            await pilot.pause()
            assert hex_view.display_mode == "2B"

            from textual.events import MouseUp

            # WORD mode: group width = 2*2+1 = 5 chars, first group x=10..14
            hex_view.on_mouse_up(MouseUp(hex_view, 10, 0, 0, 0, 1, False, False, False))
            await pilot.pause()
            assert hex_view.cursor == 0

            hex_view.on_mouse_up(MouseUp(hex_view, 14, 0, 0, 0, 1, False, False, False))
            await pilot.pause()
            assert hex_view.cursor == 0

            hex_view.on_mouse_up(MouseUp(hex_view, 15, 0, 0, 0, 1, False, False, False))
            await pilot.pause()
            assert hex_view.cursor == 2

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_delete_byte_in_insert_mode() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            assert hex_view.cursor == 0
            assert app._buffer.size == 8

            await pilot.press("l", "l")  # cursor at 'C' (offset 2)
            await pilot.pause()
            assert hex_view.cursor == 2

            await pilot.press("insert")  # enter INSERT mode
            await pilot.pause()
            assert hex_view.edit_mode == "INSERT"

            await pilot.press("delete")  # remove byte at cursor
            await pilot.pause()
            assert app._buffer.size == 7
            assert hex_view.cursor == 2
            assert app._buffer.read(0, 7) == b"ABDEFGH"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_display_mode_and_endian_switch() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            assert hex_view.display_mode == "1B"
            assert hex_view.endian == "LE"

            await pilot.press("4")
            await pilot.pause()
            assert hex_view.display_mode == "4B"
            content = str(hex_view._Static__content)
            assert "78563412" in content
            assert "F0DEBC9A" in content

            await pilot.press("b")
            await pilot.pause()
            assert hex_view.endian == "BE"
            content = str(hex_view._Static__content)
            assert "12345678" in content
            assert "9ABCDEF0" in content

            await pilot.press("2")
            await pilot.pause()
            assert hex_view.display_mode == "2B"
            content = str(hex_view._Static__content)
            assert "1234" in content
            assert "5678" in content

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_cursor_moves_by_group_size() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"A" * 64)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            assert hex_view.cursor == 0

            await pilot.press("4")
            await pilot.pause()
            await pilot.press("l")
            await pilot.pause()
            assert hex_view.cursor == 4
            await pilot.press("l")
            await pilot.pause()
            assert hex_view.cursor == 8
            await pilot.press("h")
            await pilot.pause()
            assert hex_view.cursor == 4

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_group_replace_and_insert() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"\x00" * 8)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("4")
            await pilot.pause()
            await pilot.press("e")  # enter REPLACE mode
            await pilot.pause()
            assert hex_view.edit_mode == "REPLACE"

            await pilot.press("1", "1", "2", "2", "3", "3", "4", "4")
            await pilot.pause()
            # LE 0x11223344 is stored as 44 33 22 11
            assert app._buffer.read(0, 8) == b"\x44\x33\x22\x11\x00\x00\x00\x00"
            assert hex_view.cursor == 4

            await pilot.press("insert")  # switch to INSERT mode
            await pilot.pause()
            assert hex_view.edit_mode == "INSERT"

            await pilot.press("5", "5", "6", "6", "7", "7", "8", "8")
            await pilot.pause()
            assert app._buffer.size == 12
            assert app._buffer.read(0, 12) == b"\x44\x33\x22\x11\x88\x77\x66\x55\x00\x00\x00\x00"
            assert hex_view.cursor == 8

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_digit_keys_are_hex_input_in_replace_mode() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCD")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("e")
            await pilot.pause()
            assert hex_view.edit_mode == "REPLACE"

            await pilot.press("4")
            await pilot.pause()
            assert hex_view.display_mode == "1B"
            assert hex_view.pending_str == "4"

            await pilot.press("escape")
            await pilot.pause()
            assert hex_view.edit_mode == "VIEW"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_last_row_base_address_is_aligned() -> None:
    size = 1000
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"\x00" * size)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("end")
            await pilot.pause()
            assert hex_view.cursor == size - 1
            content = str(hex_view._Static__content)
            first_line = content.splitlines()[0]
            first_addr = int(first_line[:8], 16)
            assert first_addr % 16 == 0, f"first visible row address is unaligned: 0x{first_addr:08X}"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_scrolling_down_does_not_jump_to_end() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"\x00" * 200)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            # Force a small viewport so we can test scrolling behavior.
            hex_view._page_rows = 4
            hex_view._ensure_visible()
            hex_view.refresh_view()

            # Cursor at start; first visible row is 0x00000000.
            assert hex_view.cursor == 0
            first_line = str(hex_view._Static__content).splitlines()[0]
            assert first_line.startswith("00000000")

            # Move down across the bottom row of the viewport (to row 4).
            for _ in range(4):
                await pilot.press("j")
                await pilot.pause()
            assert hex_view.cursor == 64
            first_line = str(hex_view._Static__content).splitlines()[0]
            # Should have scrolled down by exactly one row, not to the end.
            assert first_line.startswith("00000010"), f"unexpected first row: {first_line[:8]}"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_page_down_does_not_jump_to_end() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"\x00" * 400)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            hex_view._page_rows = 4
            hex_view._ensure_visible()
            hex_view.refresh_view()

            await pilot.press("pagedown")
            await pilot.pause()
            first_line = str(hex_view._Static__content).splitlines()[0]
            # Should scroll down by at least one row but not to the final page.
            assert first_line.startswith("00000010"), f"unexpected first row: {first_line[:8]}"
            assert not first_line.startswith("00000180"), "pagedown jumped to the last page"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_tab_toggles_hex_ascii_workspace() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            assert hex_view.workspace == "HEX"

            # Tab only switches workspace in edit mode
            await pilot.press("tab")
            await pilot.pause()
            assert hex_view.workspace == "HEX"

            await pilot.press("e")  # enter REPLACE mode
            await pilot.pause()
            await pilot.press("tab")
            await pilot.pause()
            assert hex_view.workspace == "ASCII"

            await pilot.press("tab")
            await pilot.pause()
            assert hex_view.workspace == "HEX"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_ascii_replace_edits_byte() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("l", "l")  # cursor at 'C' (offset 2)
            await pilot.pause()
            assert hex_view.cursor == 2

            await pilot.press("e")  # enter REPLACE mode
            await pilot.pause()
            assert hex_view.edit_mode == "REPLACE"

            await pilot.press("tab")  # switch to ASCII workspace
            await pilot.pause()
            assert hex_view.workspace == "ASCII"

            await pilot.press("z")  # replace byte at cursor with 'z'
            await pilot.pause()
            assert app._buffer.read(0, 8) == b"ABzDEFGH"
            assert hex_view.cursor == 3

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_ascii_insert_inserts_byte() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")

            await pilot.press("insert")  # enter INSERT mode
            await pilot.pause()
            assert hex_view.edit_mode == "INSERT"

            await pilot.press("tab")  # switch to ASCII workspace
            await pilot.pause()
            assert hex_view.workspace == "ASCII"

            await pilot.press("z")  # insert 'z' at cursor
            await pilot.pause()
            assert app._buffer.size == 9
            assert app._buffer.read(0, 9) == b"zABCDEFGH"
            assert hex_view.cursor == 1

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_ascii_workspace_forces_byte_mode() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("4")
            await pilot.pause()
            assert hex_view.display_mode == "4B"

            await pilot.press("e")  # enter REPLACE mode
            await pilot.pause()
            await pilot.press("tab")
            await pilot.pause()
            assert hex_view.workspace == "ASCII"
            assert hex_view.display_mode == "1B"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_non_printable_ignored_in_ascii_workspace() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("e", "tab")
            await pilot.pause()
            assert hex_view.workspace == "ASCII"
            assert hex_view.edit_mode == "REPLACE"

            original = app._buffer.read(0, 8)
            await pilot.press("escape")  # Escape is not printable
            await pilot.pause()
            assert app._buffer.read(0, 8) == original

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_digits_are_ascii_input_in_ascii_workspace() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("e", "tab")
            await pilot.pause()
            assert hex_view.workspace == "ASCII"
            assert hex_view.display_mode == "1B"

            # In ASCII edit mode digits are typed, not display-mode switches
            await pilot.press("2")
            await pilot.pause()
            assert hex_view.display_mode == "1B"
            assert app._buffer.read(0, 1) == b"2"

            # Switch back to HEX workspace and return to VIEW to change display mode
            await pilot.press("tab")
            await pilot.pause()
            assert hex_view.workspace == "HEX"

            await pilot.press("escape")
            await pilot.pause()
            assert hex_view.edit_mode == "VIEW"

            await pilot.press("2")
            await pilot.pause()
            assert hex_view.display_mode == "2B"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_ascii_input_overrides_shortcuts_in_edit_mode() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"A" * 256)
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            await pilot.press("e")  # enter REPLACE mode
            await pilot.press("tab")  # switch to ASCII workspace
            await pilot.pause()
            assert hex_view.workspace == "ASCII"
            assert hex_view.edit_mode == "REPLACE"
            assert hex_view.cursor == 0

            # In ASCII edit mode h/j/k/l are typed as ASCII, not navigation
            await pilot.press("h")
            await pilot.pause()
            assert app._buffer.read(0, 1) == b"h"
            assert hex_view.cursor == 1

            await pilot.press("j")
            await pilot.pause()
            assert app._buffer.read(1, 1) == b"j"
            assert hex_view.cursor == 2

            # Arrows still navigate
            await pilot.press("left")
            await pilot.pause()
            assert hex_view.cursor == 1
            await pilot.press("down")
            await pilot.pause()
            assert hex_view.cursor == 1 + hex_view.BYTES_PER_ROW

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_status_bar_shows_workspace() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            status = app.query_one("#status")
            content = str(status._Static__content)
            assert "HEX" in content
            assert "ASCII" not in content

            await pilot.press("e", "tab")
            await pilot.pause()
            content = str(status._Static__content)
            assert "ASCII" in content

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_tab_does_not_switch_workspace_in_view_mode() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"ABCDEFGH")
        path = f.name

    app = BinseekApp(path)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            hex_view = app.query_one("#hex")
            assert hex_view.edit_mode == "VIEW"
            assert hex_view.workspace == "HEX"

            await pilot.press("tab")
            await pilot.pause()
            assert hex_view.workspace == "HEX"

            await pilot.press("e")
            await pilot.pause()
            assert hex_view.edit_mode == "REPLACE"

            await pilot.press("tab")
            await pilot.pause()
            assert hex_view.workspace == "ASCII"

            # Escape returns to VIEW mode and HEX workspace
            await pilot.press("escape")
            await pilot.pause()
            assert hex_view.edit_mode == "VIEW"
            assert hex_view.workspace == "HEX"

    try:
        asyncio.run(_run())
    finally:
        if app._buffer:
            app._buffer.close()
        os.unlink(path)


def test_find_dialog_regex_mode() -> None:
    from textual.widgets import Checkbox, Input

    from binseek.ui.find_dialog import FindDialog

    async def _run() -> None:
        app = App()
        async with app.run_test() as pilot:
            dialog = FindDialog()
            app.push_screen(dialog)
            await pilot.pause()

            pattern_input = app.screen.query_one("#pattern", Input)
            hex_checkbox = app.screen.query_one("#hex", Checkbox)
            case_checkbox = app.screen.query_one("#case", Checkbox)
            escape_checkbox = app.screen.query_one("#escape", Checkbox)
            regex_checkbox = app.screen.query_one("#regex", Checkbox)

            pattern_input.value = ".[048C] ? [0-3]. 08"
            regex_checkbox.value = True
            hex_checkbox.value = True
            await pilot.pause()

            request = dialog._parse()
            assert request is not None
            assert request.regex is True
            assert request.hex_mode is True
            assert request.pattern == ".[048C] ? [0-3]. 08"
            assert case_checkbox.disabled is True
            assert escape_checkbox.disabled is True

            # ASCII regex: case insensitive available
            regex_checkbox.value = True
            hex_checkbox.value = False
            case_checkbox.value = True
            await pilot.pause()

            pattern_input.value = r"H.llo"
            request = dialog._parse()
            assert request is not None
            assert request.regex is True
            assert request.hex_mode is False
            assert request.case_insensitive is True

    asyncio.run(_run())


def test_file_dialog_initial_dot_resolves_and_shows_parent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp)
            dialog = FileDialog("Open", initial=".")
            assert dialog.current_dir == Path(tmp)
            entries = dialog._list_entries()
            assert any(dialog._format_entry(e) == "../" for e in entries)
        finally:
            os.chdir(original_cwd)


def test_help_dialog_static_is_scrollable() -> None:
    async def _run() -> None:
        app = App()
        async with app.run_test(size=(80, 25)) as pilot:
            dialog = HelpDialog()
            app.push_screen(dialog)
            await pilot.pause()
            scroll = dialog.query_one(VerticalScroll)
            assert scroll.virtual_size.height > scroll.container_size.height
            assert scroll.max_scroll_y > 0
            scroll.scroll_down(animate=False)
            await pilot.pause()
            assert scroll.scroll_y > 0
            static = scroll.query_one(Static)
            assert "Regex Search" in str(static.render())
            assert "Hex Regex" in str(static.render())

    asyncio.run(_run())


def test_help_text_includes_regex_sections() -> None:
    assert "Regex Search" in HELP_TEXT
    assert "Hex Regex" in HELP_TEXT
    assert r"\xNN" in HELP_TEXT

