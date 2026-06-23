"""Goto offset dialog."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class GotoDialog(ModalScreen[Optional[int]]):
    """Dialog for jumping to an absolute offset."""

    DEFAULT_CSS = """
    GotoDialog {
        align: center middle;
    }
    GotoDialog > Vertical {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    GotoDialog Label {
        margin-bottom: 1;
    }
    GotoDialog Input {
        margin-bottom: 1;
    }
    GotoDialog Horizontal {
        height: auto;
        align: right middle;
    }
    GotoDialog Button {
        margin-left: 1;
    }
    """

    def __init__(self, initial: str = "") -> None:
        super().__init__()
        self.initial = initial

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Go to offset (decimal or 0xhex):")
            yield Input(value=self.initial, id="offset")
            yield Label("", id="error")
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")

    def _parse(self) -> Optional[int]:
        text = self.query_one("#offset", Input).value.strip()
        error_label = self.query_one("#error", Label)
        try:
            value = int(text, 0)
        except ValueError:
            error_label.update("Error: invalid offset")
            return None
        if value < 0:
            error_label.update("Error: offset must be non-negative")
            return None
        error_label.update("")
        return value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            value = self._parse()
            if value is not None:
                self.dismiss(value)
        else:
            self.dismiss(None)

    def on_input_submitted(self) -> None:
        value = self._parse()
        if value is not None:
            self.dismiss(value)

    def key_escape(self) -> None:
        self.dismiss(None)
