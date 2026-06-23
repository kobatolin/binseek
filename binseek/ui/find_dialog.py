"""Find bytes dialog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label

from binseek.ui.utils import parse_pattern


@dataclass
class FindRequest:
    pattern: Union[str, bytes]
    case_insensitive: bool = False
    escape: bool = False
    regex: bool = False
    hex_mode: bool = False


class FindDialog(ModalScreen[Optional[FindRequest]]):
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
            yield Checkbox("Case insensitive", value=False, id="case")
            yield Checkbox("Escape sequences", value=False, id="escape")
            yield Checkbox("Regex", value=False, id="regex")
            yield Label("", id="error")
            with Horizontal():
                yield Button("Find", variant="primary", id="find")
                yield Button("Cancel", id="cancel")

    def _update_controls(self) -> None:
        hex_checkbox = self.query_one("#hex", Checkbox)
        case_checkbox = self.query_one("#case", Checkbox)
        escape_checkbox = self.query_one("#escape", Checkbox)
        regex_checkbox = self.query_one("#regex", Checkbox)

        if regex_checkbox.value:
            escape_checkbox.disabled = True
            escape_checkbox.value = False
            if hex_checkbox.value:
                case_checkbox.disabled = True
                case_checkbox.value = False
            else:
                case_checkbox.disabled = False
        else:
            escape_checkbox.disabled = hex_checkbox.value
            case_checkbox.disabled = hex_checkbox.value
            if hex_checkbox.value:
                case_checkbox.value = False
                escape_checkbox.value = False

    def _parse(self) -> Optional[FindRequest]:
        pattern = self.query_one("#pattern", Input).value
        hex_mode = self.query_one("#hex", Checkbox).value
        case_insensitive = self.query_one("#case", Checkbox).value
        escape = self.query_one("#escape", Checkbox).value
        regex = self.query_one("#regex", Checkbox).value
        error_label = self.query_one("#error", Label)

        if not pattern:
            error_label.update("Error: pattern is empty")
            return None

        if regex:
            if hex_mode:
                case_insensitive = False
                escape = False
            error_label.update("")
            return FindRequest(
                pattern,
                case_insensitive=case_insensitive,
                escape=False,
                regex=True,
                hex_mode=hex_mode,
            )

        try:
            data = parse_pattern(pattern, hex_mode, escape=escape)
        except ValueError as exc:
            error_label.update(f"Error: {exc}")
            return None
        if not data:
            error_label.update("Error: pattern is empty")
            return None
        error_label.update("")
        if hex_mode:
            case_insensitive = False
            escape = False
        return FindRequest(
            data,
            case_insensitive=case_insensitive,
            escape=escape,
            regex=False,
            hex_mode=hex_mode,
        )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id in ("hex", "regex"):
            self._update_controls()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "find":
            request = self._parse()
            if request is not None:
                self.dismiss(request)
        else:
            self.dismiss(None)

    def on_input_submitted(self) -> None:
        request = self._parse()
        if request is not None:
            self.dismiss(request)

    def key_escape(self) -> None:
        self.dismiss(None)
