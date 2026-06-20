"""Find bytes dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label

from binseek.ui.utils import parse_pattern


class FindDialog(ModalScreen[bytes | None]):
    """Dialog for entering a byte pattern to search."""

    DEFAULT_CSS = """
    FindDialog {
        align: center middle;
    }
    FindDialog > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    FindDialog Label {
        margin-bottom: 1;
    }
    FindDialog Input {
        margin-bottom: 1;
    }
    FindDialog Checkbox {
        margin-bottom: 1;
    }
    FindDialog Horizontal {
        height: auto;
        align: right middle;
    }
    FindDialog Button {
        margin-left: 1;
    }
    """

    def __init__(self, initial: str = "") -> None:
        super().__init__()
        self.initial = initial

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Find bytes:")
            yield Input(value=self.initial, id="pattern")
            yield Checkbox("Hex pattern", value=True, id="hex")
            yield Label("", id="error")
            with Horizontal():
                yield Button("Find", variant="primary", id="find")
                yield Button("Cancel", id="cancel")

    def _parse(self) -> bytes | None:
        pattern = self.query_one("#pattern", Input).value
        hex_mode = self.query_one("#hex", Checkbox).value
        error_label = self.query_one("#error", Label)
        try:
            data = parse_pattern(pattern, hex_mode)
        except ValueError as exc:
            error_label.update(f"Error: {exc}")
            return None
        if not data:
            error_label.update("Error: pattern is empty")
            return None
        error_label.update("")
        return data

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "find":
            data = self._parse()
            if data is not None:
                self.dismiss(data)
        else:
            self.dismiss(None)

    def on_input_submitted(self) -> None:
        data = self._parse()
        if data is not None:
            self.dismiss(data)

    def key_escape(self) -> None:
        self.dismiss(None)
