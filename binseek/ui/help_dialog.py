"""Help dialog showing keyboard shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


HELP_TEXT = """Menu (function keys)
  F1                            Help
  F2                            Open
  F3                            Find
  F4                            Save
  F5                            Save As
  F6                            Replace
  F7                            Goto
  F8                            Quit

Original control shortcuts
  Ctrl+O                        Open
  Ctrl+S                        Save
  Ctrl+Shift+S                  Save As
  Ctrl+F                        Find
  Ctrl+H                        Replace
  Ctrl+G                        Goto
  Ctrl+Q                        Quit

Navigation
  Arrows / HJKL                 Move cursor (H left, J down, K up, L right)
  PageUp / PageDown             Scroll by page
  Home / End                    Go to start / end of file
  1 / 2 / 4                     Switch 1B/2B/4B display mode (VIEW mode)
  B                             Toggle big/little endian (VIEW mode)

Search results
  F9 / Shift+F9                 Next / previous result

Editing
  E                             Toggle REPLACE mode
  Insert                        Toggle INSERT mode
  Delete                        Delete byte at cursor (INSERT mode)
  Esc                           Return to VIEW mode
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
