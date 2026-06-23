"""Simple confirmation dialog with multiple choices."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDialog(ModalScreen[Optional[str]]):
    """A modal dialog that returns the user's choice."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }
    ConfirmDialog > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    ConfirmDialog Label {
        margin-bottom: 1;
    }
    ConfirmDialog Horizontal {
        height: auto;
        align: center middle;
    }
    ConfirmDialog Button {
        margin: 0 1;
    }
    ConfirmDialog Button:focus {
        background-tint: $foreground 25%;
        text-style: bold;
    }
    """

    def __init__(
        self,
        message: str,
        save_text: str = "Save & Quit",
        discard_text: str = "Discard & Quit",
    ) -> None:
        super().__init__()
        self.message = message
        self.save_text = save_text
        self.discard_text = discard_text

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.message)
            with Horizontal():
                yield Button(self.save_text, variant="primary", id="save")
                yield Button(self.discard_text, id="discard")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        buttons = list(self.query("Horizontal Button"))
        if buttons:
            buttons[0].focus()

    def _buttons(self) -> list[Button]:
        return list(self.query("Horizontal > Button"))

    def _move_button_focus(self, delta: int) -> None:
        buttons = self._buttons()
        if not buttons:
            return
        try:
            current = buttons.index(self.screen.focused)
        except (ValueError, TypeError):
            current = 0
        else:
            current = max(0, min(len(buttons) - 1, current + delta))
        buttons[current].focus()

    def key_left(self, event: Key) -> None:
        self._move_button_focus(-1)
        event.stop()

    def key_right(self, event: Key) -> None:
        self._move_button_focus(1)
        event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.dismiss("save")
        elif event.button.id == "discard":
            self.dismiss("discard")
        else:
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)
