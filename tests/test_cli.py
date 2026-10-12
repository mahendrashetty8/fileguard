"""Tests for FileGuard CLI argument parsing and command routing."""

from pathlib import Path
import pytest

from fileguard import exit_codes
from fileguard.cli import build_parser, main


def test_cli_help(capsys):
    """Verify --help displays main usage, commands, and options."""
    exit_code = main(["--help"])
    assert exit_code == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "usage: fileguard" in captured.out
    assert "scan" in captured.out
    assert "organize" in captured.out
    assert "validate" in captured.out
    assert "-h, --help" in captured.out


def test_cli_no_args_displays_help(capsys):
    """Verify running fileguard with no arguments displays help."""
    exit_code = main([])
    assert exit_code == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "usage: fileguard" in captured.out


def test_cli_version(capsys):
    """Verify --version displays program version."""
    exit_code = main(["--version"])
    assert exit_code == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "fileguard" in captured.out


def test_cli_scan_help(capsys):
    """Verify scan --help displays command description."""
    exit_code = main(["scan", "--help"])
    assert exit_code == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "usage: fileguard scan" in captured.out
    assert "directory" in captured.out


def test_cli_organize_help(capsys):
    """Verify organize --help displays dry-run, force, and verbose options."""
    exit_code = main(["organize", "--help"])
    assert exit_code == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "usage: fileguard organize" in captured.out
    assert "--dry-run" in captured.out
    assert "--force" in captured.out
    assert "--verbose" in captured.out


def test_cli_validate_help(capsys):
    """Verify validate --help displays command description."""
    exit_code = main(["validate", "--help"])
    assert exit_code == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "usage: fileguard validate" in captured.out
    assert "directory" in captured.out


def test_cli_invalid_command(capsys):
    """Verify unrecognized command exits with INVALID_ARGUMENT (2)."""
    exit_code = main(["invalid_cmd", "some_dir"])
    assert exit_code == exit_codes.INVALID_ARGUMENT
    captured = capsys.readouterr()
    assert "Error: Invalid command or option." in captured.err


def test_cli_missing_argument(capsys):
    """Verify missing required directory argument exits with INVALID_ARGUMENT (2)."""
    exit_code = main(["scan"])
    assert exit_code == exit_codes.INVALID_ARGUMENT
    captured = capsys.readouterr()
    assert "Error: Missing required argument: directory" in captured.err


def test_cli_missing_directory_exit_code(tmp_path: Path, capsys):
    """Verify non-existent directory returns FILE_NOT_FOUND (3)."""
    missing_dir = tmp_path / "does_not_exist"
    exit_code = main(["scan", str(missing_dir)])
    assert exit_code == exit_codes.FILE_NOT_FOUND
    captured = capsys.readouterr()
    assert "Error: Directory not found." in captured.err
    assert "Traceback" not in captured.err


def test_cli_file_instead_of_directory_exit_code(tmp_path: Path, capsys):
    """Verify file path given instead of directory returns INVALID_ARGUMENT (2)."""
    sample_file = tmp_path / "sample.pdf"
    sample_file.write_text("dummy")
    exit_code = main(["organize", str(sample_file)])
    assert exit_code == exit_codes.INVALID_ARGUMENT
    captured = capsys.readouterr()
    assert "Error: Expected a directory." in captured.err
    assert "Traceback" not in captured.err


def test_cli_full_workflow_scan_organize_validate(tmp_path: Path, capsys):
    """End-to-end test of scan, organize, and validate commands on a temporary folder."""
    # Populate tmp_path
    (tmp_path / "pic.png").write_text("image")
    (tmp_path / "notes.txt").write_text("text")

    # 1. Scan
    code_scan = main(["scan", str(tmp_path)])
    assert code_scan == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "Files found: 2" in captured.out

    # 2. Validate
    code_val = main(["validate", str(tmp_path)])
    assert code_val == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "Validation successful." in captured.out

    # 3. Organize with dry-run
    code_dry = main(["organize", str(tmp_path), "--dry-run"])
    assert code_dry == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "No files were changed." in captured.out

    # 4. Actual Organize
    code_org = main(["organize", str(tmp_path)])
    assert code_org == exit_codes.SUCCESS
    captured = capsys.readouterr()
    assert "Organization completed successfully." in captured.out
    assert (tmp_path / "Images" / "pic.png").exists()
    assert (tmp_path / "Documents" / "notes.txt").exists()
