"""Tests for the command-line interface."""

from __future__ import annotations

import sys
from io import StringIO
from unittest import mock

import pytest

from binseek import __version__
from binseek.app import main


def test_cli_version_exits_with_version_string() -> None:
    with pytest.raises(SystemExit) as exc_info:
        with mock.patch.object(sys, "argv", ["binseek", "--version"]):
            main()
    assert exc_info.value.code == 0


def test_cli_help_exits_with_usage() -> None:
    with pytest.raises(SystemExit) as exc_info:
        with mock.patch.object(sys, "argv", ["binseek", "--help"]):
            main()
    assert exc_info.value.code == 0


def test_cli_unknown_argument_exits_with_error(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as exc_info:
        with mock.patch.object(sys, "argv", ["binseek", "--unknown"]):
            main()
    assert exc_info.value.code == 2


def test_cli_version_short_flag() -> None:
    with pytest.raises(SystemExit) as exc_info:
        with mock.patch.object(sys, "argv", ["binseek", "-v"]):
            main()
    assert exc_info.value.code == 0
