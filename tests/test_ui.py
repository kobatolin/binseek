"""Tests for the Textual UI widgets."""

from __future__ import annotations

import asyncio
import os
import tempfile

from textual.app import App
from textual.widgets import Button

from binseek.app import BinseekApp
from binseek.ui.confirm_dialog import ConfirmDialog
from binseek.ui.help_dialog import HELP_TEXT


def test_hex_view_shows_shortcuts_when_no_file_open() -> None:
    async def _run() -> None:
        app = BinseekApp()
        async with app.run_test() as pilot:
            hex_view = app.query_one("#hex")
            content = str(hex_view._Static__content)
            assert "No file open" in content
            assert HELP_TEXT.strip() in content.strip()

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
