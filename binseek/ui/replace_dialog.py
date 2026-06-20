"""Replace bytes dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label

from binseek.ui.utils import parse_pattern


class ReplaceDialog(ModalScreen[tuple[bytes, bytes, bool] | None]):
    """Dialog for entering find/replace byte patterns."""

    DEFAULT_CSS = """
    ReplaceDialog {
        align: center middle;
    }
    ReplaceDialog > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    ReplaceDialog Label {
        margin-bottom: 1;
    }
    ReplaceDialog Input {
        margin-bottom: 1;
    }
    ReplaceDialog Checkbox {
        margin-bottom: 1;
    }
    ReplaceDialog Horizontal {
        height: auto;
        align: right middle;
    }
    ReplaceDialog Button {
        margin-left: 1;
    }
    """

    def __init__(self, find_initial: str = "", replace_initial: str = "") -> None:
        super().__init__()
        self.find_initial = find_initial
        self.replace_initial = replace_initial

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Find bytes:")
            yield Input(value=self.find_initial, id="find")
            yield Checkbox("Hex pattern", value=True, id="find-hex")
            yield Label("Replace bytes:")
            yield Input(value=self.replace_initial, id="replace")
            yield Checkbox("Hex pattern", value=True, id="replace-hex")
            yield Label("", id="error")
            with Horizontal():
                yield Button("Replace", id="replace-btn")
                yield Button("Replace All", id="replace-all")
                yield Button("Cancel", id="cancel")

    def _parse(self) -> tuple[bytes, bytes] | None:
        find_text = self.query_one("#find", Input).value
        replace_text = self.query_one("#replace", Input).value
        find_hex = self.query_one("#find-hex", Checkbox).value
        replace_hex = self.query_one("#replace-hex", Checkbox).value
        error_label = self.query_one("#error", Label)
        try:
            find = parse_pattern(find_text, find_hex)
            replace = parse_pattern(replace_text, replace_hex)
        except ValueError as exc:
            error_label.update(f"Error: {exc}")
            return None
        if not find:
            error_label.update("Error: find pattern is empty")
            return None
        error_label.update("")
        return find, replace

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        parsed = self._parse()
        if parsed is None:
            return
        find, replace = parsed
        all_flag = event.button.id == "replace-all"
        self.dismiss((find, replace, all_flag))

    def key_escape(self) -> None:
        self.dismiss(None)
