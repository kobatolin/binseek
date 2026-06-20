---
name: binseek-test
description: Automated testing workflow for the binseek project (Python + C++ hybrid, WSL cross-compile). Use when the user asks to run tests, verify changes, perform CI-like validation, or check that the C++ core and Python code still work after modifications.
---

# binseek-test

Run the full test suite for binseek and report results.

## Workflow

1. Build the C++ core for both target platforms:
   - `wsl make linux`
   - `wsl make windows`
2. Run the C++ self-tests:
   - `wsl make test-cpp`
3. Run the Python tests:
   - Windows host (with venv): `.venv\Scripts\python -m pytest tests -q`
   - WSL / Linux: `python3 -m pytest tests -q`
4. If any step fails, stop and report the failing command and output.

## Bundled script

To run the whole suite with one command from the project root:

```bash
python .agents/skills/binseek-test/scripts/run-tests.py
```

The script automatically locates the project venv Python (`.venv/Scripts/python.exe` or `.venv/bin/python`) and falls back to `python3`/`sys.executable`.

## Notes

- The Windows DLL is cross-compiled inside WSL using `x86_64-w64-mingw32-g++`.
- The Linux `.so` is built with WSL `g++`.
- If `wsl` is not available, report that the hybrid build cannot run.
