"""Main Textual application for binseek."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.binding import Binding

from binseek.model.buffer import Buffer, CoreError
from binseek.ui.confirm_dialog import ConfirmDialog
from binseek.ui.file_dialog import FileDialog
from binseek.ui.find_dialog import FindDialog, FindRequest
from binseek.ui.goto_dialog import GotoDialog
from binseek.ui.help_dialog import HelpDialog
from binseek.ui.hex_view import HexView
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
            display_mode=hex_view.display_mode if hex_view else "1B",
            endian=hex_view.endian if hex_view else "LE",
            workspace=hex_view.workspace if hex_view else "HEX",
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
            start = self._buffer.path.parent if self._buffer else Path.cwd()
            self.push_screen(
                FileDialog("Open file", initial=start),
                lambda path: path and self._do_open(Path(path)),
            )

        if not self._buffer or not self._buffer.dirty:
            proceed_to_open()
            return

        def on_choice(choice: Optional[str]) -> None:
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

        def do_save(target: Path) -> None:
            try:
                self._buffer.save(target)
            except CoreError as exc:
                self.notify(f"Save failed: {exc}", severity="error")
                return
            self.refresh_status()
            self.notify(f"Saved {target}")

        def on_path(path: Optional[str]) -> None:
            if not path:
                return
            target = Path(path)
            if target.exists() and target.resolve() != self._buffer.path.resolve():

                def on_choice(choice: Optional[str]) -> None:
                    if choice == "save":
                        do_save(target)

                self.push_screen(
                    ConfirmDialog(
                        f"{target.name} already exists. Overwrite?",
                        save_text="Overwrite",
                        discard_text="Cancel",
                    ),
                    on_choice,
                )
            else:
                do_save(target)

        self.push_screen(
            FileDialog(
                "Save As",
                initial=self._buffer.path.parent,
                default_name=self._buffer.path.name,
                save_mode=True,
            ),
            on_path,
        )

    def _do_find(self, request: Optional[FindRequest]) -> None:
        if not self._buffer or request is None:
            return
        if request.regex:
            assert isinstance(request.pattern, str)
            results = self._buffer.search_regex(
                request.pattern,
                hex_mode=request.hex_mode,
                case_insensitive=request.case_insensitive,
            )
        else:
            assert isinstance(request.pattern, bytes)
            results = self._buffer.search(
                request.pattern,
                case_insensitive=request.case_insensitive,
            )
        hex_view = self.query_one(HexView)
        if not results:
            hex_view.clear_search_results()
            self.notify("Pattern not found", severity="warning")
            return
        hex_view.set_search_results(results, results[0][0])
        hex_view.jump_to(results[0][0])
        self.notify(f"Found {len(results)} occurrence(s)")

    def action_find(self) -> None:
        if not self._buffer:
            self.notify("No file open", severity="warning")
            return
        self.push_screen(FindDialog(), self._do_find)

    def action_find_next(self) -> None:
        if not self._buffer:
            return
        match = self._buffer.search_next()
        if match is None:
            self.notify("No more occurrences", severity="warning")
            return
        offset, _length = match
        hex_view = self.query_one(HexView)
        hex_view.set_search_results(self._buffer._search_results, offset)
        hex_view.jump_to(offset)

    def action_find_prev(self) -> None:
        if not self._buffer:
            return
        match = self._buffer.search_prev()
        if match is None:
            self.notify("No previous occurrences", severity="warning")
            return
        offset, _length = match
        hex_view = self.query_one(HexView)
        hex_view.set_search_results(self._buffer._search_results, offset)
        hex_view.jump_to(offset)

    def _do_replace(self, find: bytes, replace: bytes, replace_all: bool) -> None:
        if not self._buffer:
            return
        hex_view = self.query_one(HexView)
        if replace_all:
            results = self._buffer.search(find, max_results=100_000, case_insensitive=False)
            if not results:
                self.notify("Pattern not found", severity="warning")
                return
            for offset, length in reversed(results):
                try:
                    self._buffer.replace(offset, length, replace)
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
                results = self._buffer.search(find, case_insensitive=False)
                if not results:
                    self.notify("Pattern not found", severity="warning")
                    return
                current = results[0]
            offset, length = current
            try:
                self._buffer.replace(offset, length, replace)
            except CoreError as exc:
                self.notify(f"Replace failed: {exc}", severity="error")
                return
            # Refresh search so the next replace moves on.
            results = self._buffer.search(find, case_insensitive=False)
            hex_view.set_search_results(results, offset)
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

        def on_offset(offset: Optional[int]) -> None:
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

        def on_choice(choice: Optional[str]) -> None:
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
    import argparse
    import sys

    from binseek import __version__

    parser = argparse.ArgumentParser(
        prog="binseek",
        description="A TUI binary file viewer, searcher and editor.",
    )
    parser.add_argument("file", nargs="?", help="file to open")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args()

    app = BinseekApp(args.file)
    app.run()


if __name__ == "__main__":
    main()
