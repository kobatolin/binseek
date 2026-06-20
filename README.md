# binseek

A fast, keyboard-driven **TUI binary file viewer, searcher and editor**.

- Pure TUI — no GUI dependency
- Cross-platform: x86-64 Windows & Linux
- Menu bar + keyboard shortcuts
- Large files open instantly via memory-mapped IO
- Python 3.13 + [Textual](https://textual.textualize.io/) for the UI
- C++17 core for IO, search and edit operations, compiled as a shared library

## Features

- Open files of any size via memory mapping
- Hex + ASCII page view with keyboard navigation
- Direct editing modes:
  - **VIEW** (default): navigate
  - **REPLACE** (`E`): type two hex digits to overwrite the byte under the cursor
  - **INSERT** (`Insert`): type two hex digits to insert a new byte at the cursor
  - Press `Esc` to return to VIEW mode
- Find bytes (hex or text) with result highlighting
- Replace single or all occurrences
- Go to absolute offset
- Save in-place or save-as

## Shortcuts

| Key | Action |
|---|---|
| `F1` | Help |
| `F2` | Open file |
| `F3` | Find |
| `F4` | Save |
| `F5` | Save As |
| `F6` | Replace |
| `F7` | Go to offset |
| `F8` | Quit |
| `F9` / `Shift+F9` | Next / previous result |
| `Ctrl+O` / `Ctrl+S` / `Ctrl+Shift+S` | Open / Save / Save As |
| `Ctrl+F` / `Ctrl+H` / `Ctrl+G` / `Ctrl+Q` | Find / Replace / Goto / Quit |
| `E` | Toggle REPLACE mode |
| `Insert` | Toggle INSERT mode |
| `Esc` | Return to VIEW mode |
| Arrows / PageUp / PageDown | Navigate hex view |

## Build

The C++ core is built with Make. The Windows DLL is cross-compiled inside WSL using mingw-w64.

```bash
# Linux shared library
make linux

# Windows DLL (requires x86_64-w64-mingw32-g++)
make windows

# Both
make all

# Clean
make clean
```

On Windows you can invoke the WSL build from PowerShell/CMD:

```powershell
wsl make linux
wsl make windows
```

## Run

Create a virtual environment and install the Python dependency:

```bash
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Start binseek:

```bash
python -m binseek [file]
```

## Test

```bash
# C++ self-tests
make test-cpp

# Python tests (pytest required)
pip install -r requirements-dev.txt
python -m pytest tests -q

# Or run everything with a specific Python interpreter
make test PYTHON=.venv/bin/python3
```

## Project Layout

```
binseek/
├── binseek/         # Python package (UI + model + ctypes binding)
├── src/cpp/         # C++ core (mmap, search, editor, C API)
├── tests/           # pytest + C++ self-tests
├── Makefile
├── pyproject.toml
└── requirements.txt
```

## License

MIT
