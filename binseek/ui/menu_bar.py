"""Top menu bar for binseek."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button


class MenuButton(Button):
    """A menu button that does not steal focus from the hex view."""

    can_focus = False


class MenuBar(Horizontal):
    """Horizontal bar with top-level menu actions."""

    DEFAULT_CSS = """
    MenuBar {
        height: auto;
        dock: top;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    MenuButton {
        min-width: 8;
        height: auto;
        border: none;
        background: $surface;
        color: $text;
        padding: 0 1;
        content-align: center middle;
    }
    MenuButton:hover {
        background: $surface-lighten-1;
    }
    """

    def compose(self) -> ComposeResult:
        yield MenuButton("Open", id="btn-open")
        yield MenuButton("Save", id="btn-save")
        yield MenuButton("Save As", id="btn-save-as")
        yield MenuButton("Find", id="btn-find")
        yield MenuButton("Replace", id="btn-replace")
        yield MenuButton("Goto", id="btn-goto")
        yield MenuButton("Quit", id="btn-quit")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "btn-open": "open",
            "btn-save": "save",
            "btn-save-as": "save_as",
            "btn-find": "find",
            "btn-replace": "replace",
            "btn-goto": "goto",
            "btn-quit": "quit",
        }
        action = mapping.get(event.button.id)
        if action:
            await self.app.run_action(action)
