import asyncio
import tempfile
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Label, ListView
from ui.file_dialog import FileDialog


class DummyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Label("test")


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "subdir").mkdir()
        (root / "file.txt").write_text("hello")

        app = DummyApp()
        async with app.run_test(size=(80, 30)) as pilot:
            await app.push_screen(FileDialog("Open", initial=root))
            await pilot.pause()
            screen = app.screen
            list_view = screen.query_one("#file-list", ListView)
            items = [str(item.children[0].renderable) for item in list_view.children]
            print("items:", items)
            assert "[D] subdir/" in items
            assert "[F] file.txt" in items

            # Navigate into subdir
            list_view.index = items.index("[D] subdir/")
            await pilot.press("enter")
            await pilot.pause()
            label = screen.query_one("#current-dir", Label)
            print("dir after enter:", label.renderable)
            assert "subdir" in str(label.renderable)

            # Go up
            list_view = screen.query_one("#file-list", ListView)
            list_view.index = 0  # "../"
            await pilot.press("enter")
            await pilot.pause()
            label = screen.query_one("#current-dir", Label)
            print("dir after up:", label.renderable)
            assert str(root) in str(label.renderable)

            # Select file
            list_view = screen.query_one("#file-list", ListView)
            items = [str(item.children[0].renderable) for item in list_view.children]
            list_view.index = items.index("[F] file.txt")
            result = None

            def callback(value: str | None) -> None:
                nonlocal result
                result = value

            screen.dismiss = callback  # type: ignore[assignment]
            await pilot.press("enter")
            await pilot.pause()
            print("selected:", result)
            assert result is not None
            assert "file.txt" in result

    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
