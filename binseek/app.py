"""Main Textual application for binseek."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.binding import Binding

from binseek.model.buffer import Buffer, CoreError
from binseek.ui.confirm_dialog import ConfirmDialog
from binseek.ui.find_dialog import FindDialog
from binseek.ui.goto_dialog import GotoDialog
from binseek.ui.help_dialog import HelpDialog
from binseek.ui.hex_view import HexView
from binseek.ui.input_dialog import InputDialog
from binseek.ui.menu_bar import MenuBar
from binseek.ui.replace_dialog import ReplaceDialog
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
        # Function keys (added without removing existing shortcuts)
        Binding("f1", "help", "Help"),
        Binding("f2", "open", "Open"),
        Binding("f3", "find", "Find"),
        Binding("f4", "save", "Save"),
        Binding("f5", "save_as", "Save As"),
        Binding("f6", "replace", "Replace"),
        Binding("f7", "goto", "Goto"),
        Binding("f8", "quit", "Quit"),
        Binding("f9", "find_next", "Find Next"),
        Binding("shift+f9", "find_prev", "Find Prev"),
        # Original control shortcuts
        Binding("ctrl+o", "open", "Open"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+shift+s", "save_as", "Save As"),
        Binding("ctrl+f", "find", "Find"),
        Binding("ctrl+h", "replace", "Replace"),
        Binding("ctrl+g", "goto", "Goto"),
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
            mode=hex_view.edit_mode if hex_view else "VIEW",
            path=str(self._buffer.path),
            size=self._buffer.size,
            offset=hex_view.cursor if hex_view else 0,
            dirty=self._buffer.dirty,
            pending=hex_view.pending_str if hex_view else "",
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
        def proceed_to_open() -> None:
            def on_path(path: str | None) -> None:
                if path:
                    self._do_open(Path(path))

            self.push_screen(InputDialog("Open file path:"), on_path)

        if not self._buffer or not self._buffer.dirty:
            proceed_to_open()
            return

        def on_choice(choice: str | None) -> None:
            if choice == "save":
                try:
                    self._buffer.save()
                except CoreError as exc:
                    self.notify(f"Save failed: {exc}", severity="error")
                    return
                self.refresh_status()
                self.notify(f"Saved {self._buffer.path}")
                proceed_to_open()
            elif choice == "discard":
                proceed_to_open()
            # Cancel: stay with current file

        self.push_screen(
            ConfirmDialog(
                "File has unsaved changes. Open another file?",
                save_text="Save & Open",
                discard_text="Discard & Open",
            ),
            on_choice,
        )

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

    def _do_find(self, pattern: bytes) -> None:
        if not self._buffer:
            return
        results = self._buffer.search(pattern)
        hex_view = self.query_one(HexView)
        if not results:
            hex_view.clear_search_results()
            self.notify("Pattern not found", severity="warning")
            return
        hex_view.set_search_results(results, results[0])
        hex_view.jump_to(results[0])
        self.notify(f"Found {len(results)} occurrence(s)")

    def action_find(self) -> None:
        if not self._buffer:
            self.notify("No file open", severity="warning")
            return
        self.push_screen(FindDialog(), self._do_find)

    def action_find_next(self) -> None:
        if not self._buffer:
            return
        offset = self._buffer.search_next()
        if offset is None:
            self.notify("No more occurrences", severity="warning")
            return
        hex_view = self.query_one(HexView)
        hex_view.set_search_results(self._buffer._search_results, offset)
        hex_view.jump_to(offset)

    def action_find_prev(self) -> None:
        if not self._buffer:
            return
        offset = self._buffer.search_prev()
        if offset is None:
            self.notify("No previous occurrences", severity="warning")
            return
        hex_view = self.query_one(HexView)
        hex_view.set_search_results(self._buffer._search_results, offset)
        hex_view.jump_to(offset)

    def _do_replace(self, find: bytes, replace: bytes, replace_all: bool) -> None:
        if not self._buffer:
            return
        hex_view = self.query_one(HexView)
        if replace_all:
            results = self._buffer.search(find, max_results=100_000)
            if not results:
                self.notify("Pattern not found", severity="warning")
                return
            for offset in reversed(results):
                try:
                    self._buffer.replace(offset, len(find), replace)
                except CoreError as exc:
                    self.notify(f"Replace failed at {offset}: {exc}", severity="error")
                    return
            hex_view.clear_search_results()
            self.refresh_status()
            self.notify(f"Replaced {len(results)} occurrence(s)")
        else:
            # Replace the current search result, or find the first one.
            current = self._buffer.current_search_result()
            if current is None or self._buffer._last_pattern != find:
                results = self._buffer.search(find)
                if not results:
                    self.notify("Pattern not found", severity="warning")
                    return
                current = results[0]
            try:
                self._buffer.replace(current, len(find), replace)
            except CoreError as exc:
                self.notify(f"Replace failed: {exc}", severity="error")
                return
            # Refresh search so the next replace moves on.
            results = self._buffer.search(find)
            hex_view.set_search_results(results, current)
            hex_view.refresh_view()
            self.refresh_status()
            self.notify("Replaced one occurrence")

    def action_replace(self) -> None:
        if not self._buffer:
            self.notify("No file open", severity="warning")
            return
        self.push_screen(ReplaceDialog(), lambda r: r and self._do_replace(*r))

    def action_goto(self) -> None:
        if not self._buffer:
            self.notify("No file open", severity="warning")
            return

        def on_offset(offset: int | None) -> None:
            if offset is None:
                return
            if offset >= self._buffer.size:
                self.notify(f"Offset {offset} is beyond file size", severity="error")
                return
            self.query_one(HexView).jump_to(offset)

        self.push_screen(GotoDialog(), on_offset)

    def action_help(self) -> None:
        self.push_screen(HelpDialog())

    def _do_exit(self) -> None:
        if self._buffer:
            self._buffer.close()
            self._buffer = None
        self.exit()

    def action_quit(self) -> None:
        if not self._buffer or not self._buffer.dirty:
            self._do_exit()
            return

        def on_choice(choice: str | None) -> None:
            if choice == "save":
                try:
                    self._buffer.save()
                except CoreError as exc:
                    self.notify(f"Save failed: {exc}", severity="error")
                    return
                self.refresh_status()
                self.notify(f"Saved {self._buffer.path}")
                self._do_exit()
            elif choice == "discard":
                self._do_exit()
            # Cancel: do nothing

        self.push_screen(
            ConfirmDialog(
                "File has unsaved changes. What would you like to do?",
                save_text="Save & Quit",
                discard_text="Discard & Quit",
            ),
            on_choice,
        )


def main() -> None:
    import sys

    app = BinseekApp(sys.argv[1] if len(sys.argv) > 1 else None)
    app.run()


if __name__ == "__main__":
    main()
