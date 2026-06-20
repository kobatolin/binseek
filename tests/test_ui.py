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


