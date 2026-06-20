"""Main Textual application for binseek."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.binding import Binding

from binseek.model.buffer import Buffer, CoreError
from binseek.ui.hex_view import HexView
from binseek.ui.input_dialog import InputDialog
from binseek.ui.menu_bar import MenuBar
from binseek.ui.status_bar import StatusBar


class BinseekApp(App[None]):
    """TUI binary file viewer, searcher and editor."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #menu {
        height: auto;
        dock: top;
    }
    #main {
        height: 1fr;
    }
    #hex {
        height: 1fr;
    }
    #status {
        height: 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("ctrl+o", "open", "Open"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+shift+s", "save_as", "Save As"),
        Binding("ctrl+f", "find", "Find"),
        Binding("ctrl+h", "replace", "Replace"),
        Binding("ctrl+g", "goto", "Goto"),
        Binding("f3", "find_next", "Find Next"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, path: Optional[str | Path] = None) -> None:
        super().__init__()
        self._initial_path = Path(path) if path else None
        self._buffer: Optional[Buffer] = None

    def compose(self) -> ComposeResult:
        yield MenuBar(id="menu")
        with Vertical(id="main"):
            yield HexView(id="hex")
        yield StatusBar(id="status")

    def on_mount(self) -> None:
        hex_view = self.query_one(HexView)
        self.set_focus(hex_view)
        if self._initial_path:
            self._do_open(self._initial_path)
        else:
            self.refresh_status("No file open. Press Ctrl+O to open a file.")

    def refresh_status(self, message: str = "") -> None:
        status = self.query_one(StatusBar)
        if message:
            status.update_status(message=message)
            return
        if not self._buffer:
            status.update_status(message="No file open")
            return
        hex_view = self.query_one(HexView)
        status.update_status(
            path=str(self._buffer.path),
            size=self._buffer.size,
            offset=hex_view._cursor if hex_view else 0,
            dirty=self._buffer.dirty,
        )

    def _do_open(self, path: Path) -> None:
        if self._buffer:
            self._buffer.close()
            self._buffer = None
        try:
            self._buffer = Buffer.open(path)
        except CoreError as exc:
            self.notify(f"Failed to open {path}: {exc}", severity="error")
            return
        self.query_one(HexView).set_buffer(self._buffer)
        self.refresh_status()
        self.notify(f"Opened {path}")

    def action_open(self) -> None:
        def on_path(path: str | None) -> None:
            if path:
                self._do_open(Path(path))

        self.push_screen(InputDialog("Open file path:"), on_path)

    def action_save(self) -> None:
        if not self._buffer:
            self.notify("No file open", severity="warning")
            return
        if not self._buffer.dirty:
            self.notify("No changes to save")
            return
        try:
            self._buffer.save()
        except CoreError as exc:
            self.notify(f"Save failed: {exc}", severity="error")
            return
        self.refresh_status()
        self.notify(f"Saved {self._buffer.path}")

    def action_save_as(self) -> None:
        if not self._buffer:
            self.notify("No file open", severity="warning")
            return

        def on_path(path: str | None) -> None:
            if path:
                try:
                    self._buffer.save(Path(path))
                except CoreError as exc:
                    self.notify(f"Save failed: {exc}", severity="error")
                    return
                self.refresh_status()
                self.notify(f"Saved {path}")

        self.push_screen(InputDialog("Save as:", value=str(self._buffer.path)), on_path)

    def action_find(self) -> None:
        self.notify("Find dialog coming in M4", severity="information")

    def action_replace(self) -> None:
        self.notify("Replace dialog coming in M4", severity="information")

    def action_goto(self) -> None:
        self.notify("Goto dialog coming in M4", severity="information")

    def action_find_next(self) -> None:
        self.notify("Find next coming in M4", severity="information")

    def action_quit(self) -> None:
        if self._buffer:
            self._buffer.close()
            self._buffer = None
        self.exit()


def main() -> None:
    import sys

    app = BinseekApp(sys.argv[1] if len(sys.argv) > 1 else None)
    app.run()


if __name__ == "__main__":
    main()
