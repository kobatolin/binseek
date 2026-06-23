"""Generic one-line input dialog."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class InputDialog(ModalScreen[Optional[str]]):
    """A simple modal dialog asking the user for a single line of text."""

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }
    InputDialog > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    InputDialog Label {
        margin-bottom: 1;
    }
    InputDialog Input {
        margin-bottom: 1;
    }
    InputDialog Horizontal {
        height: auto;
        align: right middle;
    }
    InputDialog Button {
        margin-left: 1;
    }
    """

    def __init__(self, title: str, value: str = "") -> None:
        super().__init__()
        self.title = title
        self.value = value

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.title)
            yield Input(value=self.value, id="input")
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self.query_one(Input).value)
        else:
            self.dismiss(None)

    def on_input_submitted(self) -> None:
        self.dismiss(self.query_one(Input).value)

    def key_escape(self) -> None:
        self.dismiss(None)
