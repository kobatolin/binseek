"""Simple confirmation dialog with multiple choices."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDialog(ModalScreen[str | None]):
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.dismiss("save")
        elif event.button.id == "discard":
            self.dismiss("discard")
        else:
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)
