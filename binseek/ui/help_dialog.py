"""Help dialog showing keyboard shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


def _format_col(items: list[tuple[str, str]], key_width: int) -> list[str]:
    """Format a single column of key/description pairs."""
    lines: list[str] = []
    for key, desc in items:
        if not key:
            lines.append("")
        else:
            lines.append(f"  {key:<{key_width}} {desc}")
    return lines


def _build_help_text() -> str:
    """Build a compact two-column help text."""
    left = [
        ("Menu (function keys)", ""),
        ("F1", "Help"),
        ("F2", "Open"),
        ("F3", "Find"),
        ("F4", "Save"),
        ("F5", "Save As"),
        ("F6", "Replace"),
        ("F7", "Goto"),
        ("F8", "Quit"),
        ("", ""),
        ("Original shortcuts", ""),
        ("Ctrl+O", "Open"),
        ("Ctrl+S", "Save"),
        ("Ctrl+Shift+S", "Save As"),
        ("Ctrl+F", "Find"),
        ("Ctrl+H", "Replace"),
        ("Ctrl+G", "Goto"),
        ("Ctrl+Q", "Quit"),
    ]
    right = [
        ("Navigation", ""),
        ("Arrows / HJKL", "Move cursor"),
        ("PageUp / Dn", "Scroll by page"),
        ("Home / End", "Start / end"),
        ("1 / 2 / 4", "1B/2B/4B mode"),
        ("B", "Toggle endian"),
        ("", ""),
        ("Search results", ""),
        ("F9", "Next result"),
        ("Shift+F9", "Previous"),
        ("", ""),
        ("Editing", ""),
        ("E", "Toggle REPLACE"),
        ("Insert", "Toggle INSERT"),
        ("Delete", "Delete byte"),
        ("Esc", "Return to VIEW"),
    ]
    key_width = 13
    left_lines = _format_col(left, key_width)
    right_lines = _format_col(right, key_width)
    max_len = max(len(left_lines), len(right_lines))

    lines: list[str] = []
    for i in range(max_len):
        l = left_lines[i] if i < len(left_lines) else ""
        r = right_lines[i] if i < len(right_lines) else ""
        if not r:
            lines.append(l)
        else:
            lines.append(f"{l:<34}  {r}")
    return "\n".join(lines)


HELP_TEXT = _build_help_text()


class HelpDialog(ModalScreen[None]):
    """Modal help screen listing shortcuts."""

    DEFAULT_CSS = """
    HelpDialog {
        align: center middle;
    }
    HelpDialog > Vertical {
        width: 74;
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
