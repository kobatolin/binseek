"""Tests for the Textual UI widgets."""

from __future__ import annotations

import asyncio
import os
import tempfile

from binseek.app import BinseekApp
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
