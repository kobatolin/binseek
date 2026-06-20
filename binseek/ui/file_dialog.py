"""Traditional-style file chooser dialog with directory listing."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView


class FileDialog(ModalScreen[str | None]):
    """A modal file dialog that lets the user browse directories and pick a file.

    Returns the selected absolute path as a string, or ``None`` when cancelled.
    """

    DEFAULT_CSS = """
    FileDialog {
        align: center middle;
    }
    FileDialog > Vertical {
        width: 70;
        height: 30;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    FileDialog #title {
        margin-bottom: 1;
    }
    FileDialog #current-dir {
        color: $text-muted;
        margin-bottom: 1;
    }
    FileDialog #file-list {
        height: 1fr;
        border: solid $background;
        margin-bottom: 1;
    }
    FileDialog #filename {
        margin-bottom: 1;
    }
    FileDialog Horizontal {
        height: auto;
        align: right middle;
    }
    FileDialog Button {
        margin-left: 1;
    }
    """

    def __init__(
        self,
        title: str,
        initial: str | Path | None = None,
        default_name: str = "",
        save_mode: bool = False,
    ) -> None:
        super().__init__()
        self.title = title
        self.save_mode = save_mode
        self._entries: list[Path] = []

        path = Path(initial or Path.cwd()).expanduser()
        if path.is_file():
            self.current_dir = path.parent
            self.default_name = default_name or path.name
        else:
            self.current_dir = path
            self.default_name = default_name

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.title, id="title")
            yield Label(str(self.current_dir), id="current-dir", markup=False)
            yield ListView(id="file-list")
            yield Input(value=self.default_name, id="filename")
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self._refresh_list()
        self.query_one("#file-list", ListView).focus()

    def _list_entries(self) -> list[Path]:
        """Return the directory entries to show, ordered dirs-first."""
        entries: list[Path] = []
        try:
            for child in self.current_dir.iterdir():
                try:
                    if child.exists():
                        entries.append(child)
                except OSError:
                    continue
        except OSError as exc:
            self.app.notify(f"Cannot read directory: {exc}", severity="error")

        dirs = sorted((p for p in entries if p.is_dir()), key=lambda p: p.name.lower())
        files = sorted((p for p in entries if p.is_file()), key=lambda p: p.name.lower())

        result: list[Path] = []
        if self.current_dir.parent != self.current_dir:
            result.append(self.current_dir.parent)
        result.extend(dirs)
        result.extend(files)
        return result

    def _refresh_list(self) -> None:
        """Repaint the directory list."""
        list_view = self.query_one("#file-list", ListView)
        list_view.clear()
        self._entries = self._list_entries()
        for entry in self._entries:
            list_view.append(ListItem(Label(self._format_entry(entry), markup=False)))
        self.query_one("#current-dir", Label).update(str(self.current_dir))

    def _format_entry(self, entry: Path) -> str:
        if entry == self.current_dir.parent:
            return "../"
        if entry.is_dir():
            return f"[D] {entry.name}/"
        return f"[F] {entry.name}"

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Fill the filename field when a file is highlighted."""
        index = event.list_view.index
        if index is None or index < 0 or index >= len(self._entries):
            return
        entry = self._entries[index]
        if entry == self.current_dir.parent or entry.is_dir():
            return
        self.query_one("#filename", Input).value = entry.name

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Navigate into directories or confirm a file selection."""
        index = event.list_view.index
        if index is None or index < 0 or index >= len(self._entries):
            return
        entry = self._entries[index]
        if entry == self.current_dir.parent or entry.is_dir():
            self.current_dir = entry if entry.is_dir() else self.current_dir.parent
            self._refresh_list()
            return
        self.query_one("#filename", Input).value = entry.name
        self._confirm()

    def _confirm(self) -> None:
        filename = self.query_one("#filename", Input).value.strip()
        if not filename:
            self.app.notify("Please select or enter a file name", severity="warning")
            return
        target = (self.current_dir / filename).resolve()
        self.dismiss(str(target))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self._confirm()
        else:
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)
