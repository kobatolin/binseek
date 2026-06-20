#!/usr/bin/env python3
"""Run the full binseek test suite.

This script:
1. Builds the C++ core for Linux (.so) and Windows (.dll) via WSL.
2. Runs the C++ self-test binary.
3. Runs the Python pytest suite.

It expects to be executed from the binseek project root, or as part of the
project-level skill at .agents/skills/binseek-test/.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    # Skill path: .agents/skills/binseek-test/scripts/run-tests.py
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def find_python() -> Path:
    root = project_root()
    candidates = [
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("python3")


def run(cmd: list[str | Path]) -> None:
    cmd_str = " ".join(str(c) for c in cmd)
    print(f"$ {cmd_str}")
    subprocess.run(cmd, cwd=project_root(), check=True)


def main() -> int:
    if shutil.which("wsl") is None:
        print("Error: wsl is not available on this system.", file=sys.stderr)
        return 1

    try:
        run(["wsl", "make", "linux"])
        run(["wsl", "make", "windows"])
        run(["wsl", "make", "test-cpp"])
        python = find_python()
        run([python, "-m", "pytest", "tests", "-q"])
    except subprocess.CalledProcessError as exc:
        print(f"Test step failed: {exc}", file=sys.stderr)
        return exc.returncode

    print("All binseek tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
