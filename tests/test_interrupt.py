"""Tests for KeyboardInterrupt (Ctrl+C) handling and exit code 130."""

from pathlib import Path
from unittest.mock import patch
import pytest

from fileguard import exit_codes
from fileguard.cli import main
from fileguard.utils.formatter import format_interrupt


def test_main_handles_keyboard_interrupt_gracefully(capsys):
    """Verify main() catches KeyboardInterrupt, prints message, and returns 130 without traceback."""
    with patch("fileguard.cli.execute_scan", side_effect=KeyboardInterrupt):
        exit_code = main(["scan", "some_dir"])

    assert exit_code == exit_codes.INTERRUPTED
    captured = capsys.readouterr()

    # Must contain the specified interrupt message
    assert "^C" in captured.out
    assert "Operation interrupted by user." in captured.out
    assert "FileGuard stopped safely." in captured.out
    assert "No further files will be processed." in captured.out

    # Must NOT have Python traceback in stderr
    assert "Traceback" not in captured.err
    assert "KeyboardInterrupt" not in captured.err


def test_organize_command_handles_keyboard_interrupt_during_move(tmp_path: Path, capsys):
    """Verify organize stops safely upon KeyboardInterrupt during processing."""
    (tmp_path / "file1.txt").write_text("first")
    (tmp_path / "file2.txt").write_text("second")

    call_count = 0

    def mock_safe_move(src, dest, force=False):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise KeyboardInterrupt
        dest.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dest)

    with patch("fileguard.services.file_organizer.safe_move_file", side_effect=mock_safe_move):
        exit_code = main(["organize", str(tmp_path)])

    assert exit_code == exit_codes.INTERRUPTED
    captured = capsys.readouterr()

    assert "Operation interrupted by user." in captured.out
    assert "Traceback" not in captured.err


def test_format_interrupt_output():
    """Verify format_interrupt string matches specification exactly."""
    msg = format_interrupt()
    assert "^C" in msg
    assert "Operation interrupted by user." in msg
    assert "FileGuard stopped safely." in msg
    assert "No further files will be processed." in msg
