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
        min-width: 12;
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
        yield MenuButton("Open(F2)", id="btn-open")
        yield MenuButton("Save(F4)", id="btn-save")
        yield MenuButton("Save As(F5)", id="btn-save-as")
        yield MenuButton("Find(F3)", id="btn-find")
        yield MenuButton("Replace(F6)", id="btn-replace")
        yield MenuButton("Goto(F7)", id="btn-goto")
        yield MenuButton("Help(F1)", id="btn-help")
        yield MenuButton("Quit(F8)", id="btn-quit")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "btn-open": "open",
            "btn-save": "save",
            "btn-save-as": "save_as",
            "btn-find": "find",
            "btn-replace": "replace",
            "btn-goto": "goto",
            "btn-help": "help",
            "btn-quit": "quit",
        }
        action = mapping.get(event.button.id)
        if action:
            await self.app.run_action(action)
