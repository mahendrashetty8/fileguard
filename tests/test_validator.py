"""Tests for FileValidator service."""

from pathlib import Path
from unittest.mock import patch
import pytest

from fileguard.errors import DirectoryNotFoundError, InvalidInputError
from fileguard.services.file_validator import FileValidator


def test_validator_valid_directory(tmp_path: Path):
    """Verify a clean directory passes all validation checks."""
    (tmp_path / "sample.txt").write_text("hello")
    (tmp_path / "song.mp3").write_text("audio")

    validator = FileValidator()
    result = validator.validate(tmp_path)

    assert result.is_valid is True
    assert len(result.problems) == 0
    assert "Directory exists" in result.successful_checks
    assert "Directory is accessible" in result.successful_checks
    assert "Files can be scanned" in result.successful_checks
    assert "No destination conflicts found" in result.successful_checks


def test_validator_missing_directory(tmp_path: Path):
    """Verify validating a missing directory raises DirectoryNotFoundError."""
    validator = FileValidator()
    with pytest.raises(DirectoryNotFoundError):
        validator.validate(tmp_path / "non_existent_folder")


def test_validator_file_instead_of_directory(tmp_path: Path):
    """Verify validating a file raises InvalidInputError."""
    file_path = tmp_path / "dummy.txt"
    file_path.write_text("text")

    validator = FileValidator()
    with pytest.raises(InvalidInputError):
        validator.validate(file_path)


def test_validator_detects_destination_conflict(tmp_path: Path):
    """Verify validator flags pre-existing destination file conflicts."""
    # Create source file that would move to Documents/notes.txt
    (tmp_path / "notes.txt").write_text("notes")

    # Pre-create conflicting file in Documents/
    docs_dir = tmp_path / "Documents"
    docs_dir.mkdir()
    (docs_dir / "notes.txt").write_text("conflict")

    validator = FileValidator()
    result = validator.validate(tmp_path)

    assert result.is_valid is False
    assert len(result.problems) >= 1
    assert any("Destination already exists:\n   Documents/notes.txt" in p for p in result.problems)


def test_validator_detects_unreadable_file(tmp_path: Path):
    """Verify validator reports files that cannot be read."""
    file_path = tmp_path / "secret.pdf"
    file_path.write_text("secret")

    validator = FileValidator()

    # Mock check_file_readable to return False for secret.pdf
    with patch("fileguard.services.file_scanner.check_file_readable", return_value=False):
        result = validator.validate(tmp_path)

    assert result.is_valid is False
    assert any("File cannot be accessed" in p for p in result.problems)
