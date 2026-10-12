"""Tests for FileScanner service."""

from pathlib import Path
import pytest

from fileguard.errors import DirectoryNotFoundError, InvalidInputError
from fileguard.services.file_scanner import FileScanner


def test_scanner_valid_directory(tmp_path: Path):
    """Verify scanning a populated directory finds and counts files and subdirectories."""
    # Create files
    (tmp_path / "img1.png").write_text("image1")
    (tmp_path / "doc1.txt").write_text("doc1")
    (tmp_path / "vid1.mp4").write_text("vid1")
    # Create subdirectory
    sub = tmp_path / "subfolder"
    sub.mkdir()

    scanner = FileScanner()
    result = scanner.scan(tmp_path)

    assert result.total_files == 3
    assert result.total_directories == 1
    assert result.category_counts["Images"] == 1
    assert result.category_counts["Documents"] == 1
    assert result.category_counts["Videos"] == 1
    assert result.category_counts["Audio"] == 0
    assert result.category_counts["Archives"] == 0
    assert result.category_counts["Other"] == 0
    assert not result.is_empty


def test_scanner_missing_directory(tmp_path: Path):
    """Verify scanning a non-existent directory raises DirectoryNotFoundError."""
    missing = tmp_path / "non_existent_dir"
    scanner = FileScanner()

    with pytest.raises(DirectoryNotFoundError) as exc_info:
        scanner.scan(missing)

    assert exc_info.value.path == str(missing)


def test_scanner_file_instead_of_directory(tmp_path: Path):
    """Verify scanning a file instead of a directory raises InvalidInputError."""
    file_path = tmp_path / "regular_file.txt"
    file_path.write_text("content")

    scanner = FileScanner()
    with pytest.raises(InvalidInputError) as exc_info:
        scanner.scan(file_path)

    assert exc_info.value.path == str(file_path)


def test_scanner_empty_directory(tmp_path: Path):
    """Verify scanning an empty directory reports zero files and is_empty is True."""
    scanner = FileScanner()
    result = scanner.scan(tmp_path)

    assert result.total_files == 0
    assert result.total_directories == 0
    assert result.is_empty


def test_scanner_categorization_and_case_insensitivity(tmp_path: Path):
    """Verify extension mapping and uppercase extensions."""
    (tmp_path / "photo.JPG").write_text("photo")
    (tmp_path / "manual.PDF").write_text("manual")
    (tmp_path / "song.MP3").write_text("song")
    (tmp_path / "archive.ZIP").write_text("archive")
    (tmp_path / "clip.MOV").write_text("clip")
    (tmp_path / "custom.XYZ").write_text("other")

    scanner = FileScanner()
    result = scanner.scan(tmp_path)

    assert result.total_files == 6
    assert result.category_counts["Images"] == 1
    assert result.category_counts["Documents"] == 1
    assert result.category_counts["Audio"] == 1
    assert result.category_counts["Archives"] == 1
    assert result.category_counts["Videos"] == 1
    assert result.category_counts["Other"] == 1
