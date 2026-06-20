"""Tests for the Textual UI widgets."""

from __future__ import annotations

import asyncio

from binseek.app import BinseekApp
from binseek.ui.help_dialog import HELP_TEXT, HelpDialog


def test_hex_view_shows_shortcuts_when_no_file_open() -> None:
    async def _run() -> None:
        app = BinseekApp()
        async with app.run_test() as pilot:
            hex_view = app.query_one("#hex")
            content = str(hex_view._Static__content)
            assert "No file open" in content
            assert HELP_TEXT.strip() in content.strip()

    asyncio.run(_run())


def test_h_opens_help_when_no_file_open() -> None:
    async def _run() -> None:
        app = BinseekApp()
        async with app.run_test() as pilot:
            await pilot.press("h")
            assert isinstance(app.screen, HelpDialog)

    asyncio.run(_run())
