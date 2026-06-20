"""Help dialog showing keyboard shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


HELP_TEXT = """Navigation
  Arrows / PageUp / PageDown    Move cursor
  Home / End                    Go to start / end of file
  Ctrl+G                        Go to offset

File
  Ctrl+O                        Open file
  Ctrl+S                        Save
  Ctrl+Shift+S                  Save As
  Ctrl+Q                        Quit

Search & Replace
  Ctrl+F                        Find
  F3 / Shift+F3                 Next / previous result
  Ctrl+H                        Replace dialog

Editing
  E                             Toggle REPLACE mode
  Insert                        Toggle INSERT mode
  Esc                           Return to VIEW mode
  H                             Show this help
"""


class HelpDialog(ModalScreen[None]):
    """Modal help screen listing shortcuts."""

    DEFAULT_CSS = """
    HelpDialog {
        align: center middle;
    }
    HelpDialog > Vertical {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    HelpDialog Static {
        margin: 1 0;
    }
    HelpDialog Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Keyboard Shortcuts")
            yield Static(HELP_TEXT)
            yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()
