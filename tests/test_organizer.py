"""Tests for FileOrganizer service."""

from pathlib import Path
import pytest

from fileguard.errors import DirectoryNotFoundError, InvalidInputError
from fileguard.services.file_organizer import FileOrganizer


def test_organizer_normal_organization(tmp_path: Path):
    """Verify files are moved into their respective category folders."""
    photo = tmp_path / "photo.jpg"
    photo.write_text("photo data")
    doc = tmp_path / "document.pdf"
    doc.write_text("doc data")
    archive = tmp_path / "data.zip"
    archive.write_text("archive data")

    organizer = FileOrganizer()
    result = organizer.organize(tmp_path)

    assert result.total_files == 3
    assert result.moved_files == 3
    assert result.skipped_files == 0
    assert result.failed_files == 0

    # Verify files moved
    assert not photo.exists()
    assert (tmp_path / "Images" / "photo.jpg").exists()
    assert (tmp_path / "Documents" / "document.pdf").exists()
    assert (tmp_path / "Archives" / "data.zip").exists()


def test_organizer_dry_run_leaves_filesystem_untouched(tmp_path: Path):
    """Verify dry-run mode does not modify the filesystem at all."""
    photo = tmp_path / "photo.png"
    photo.write_text("png data")
    doc = tmp_path / "sheet.xlsx"
    doc.write_text("sheet data")

    organizer = FileOrganizer()
    result = organizer.organize(tmp_path, dry_run=True)

    assert result.is_dry_run is True
    assert result.total_files == 2
    assert result.moved_files == 2  # Planned moves
    assert result.failed_files == 0

    # Files must still exist in original location!
    assert photo.exists()
    assert doc.exists()
    # Destination folders must NOT have been created
    assert not (tmp_path / "Images").exists()
    assert not (tmp_path / "Documents").exists()


def test_organizer_duplicate_destination_without_force(tmp_path: Path):
    """Verify duplicate destination is skipped without --force."""
    # Create source file
    source = tmp_path / "image.png"
    source.write_text("new image data")

    # Pre-create destination file
    dest_dir = tmp_path / "Images"
    dest_dir.mkdir()
    existing_dest = dest_dir / "image.png"
    existing_dest.write_text("original image data")

    organizer = FileOrganizer()
    result = organizer.organize(tmp_path, force=False)

    assert result.total_files == 1
    assert result.moved_files == 0
    assert result.skipped_files == 1
    assert result.failed_files == 0

    # Original destination content must be preserved
    assert existing_dest.read_text() == "original image data"
    # Source file must still exist
    assert source.exists()


def test_organizer_force_mode_overwrites_duplicate(tmp_path: Path):
    """Verify --force safely replaces an existing destination file."""
    source = tmp_path / "report.pdf"
    source.write_text("updated report")

    dest_dir = tmp_path / "Documents"
    dest_dir.mkdir()
    existing_dest = dest_dir / "report.pdf"
    existing_dest.write_text("old report")

    organizer = FileOrganizer()
    result = organizer.organize(tmp_path, force=True)

    assert result.total_files == 1
    assert result.moved_files == 1
    assert result.skipped_files == 0

    # Destination should now have updated content
    assert existing_dest.read_text() == "updated report"
    assert not source.exists()


def test_organizer_unknown_extension_goes_to_other(tmp_path: Path):
    """Verify unsupported/unknown extensions are moved to 'Other/'."""
    weird_file = tmp_path / "config.unknownformat"
    weird_file.write_text("conf")

    organizer = FileOrganizer()
    result = organizer.organize(tmp_path)

    assert result.moved_files == 1
    assert (tmp_path / "Other" / "config.unknownformat").exists()


def test_organizer_empty_directory(tmp_path: Path):
    """Verify organizing an empty directory succeeds with zero files moved."""
    organizer = FileOrganizer()
    result = organizer.organize(tmp_path)

    assert result.total_files == 0
    assert result.moved_files == 0
    assert result.is_empty is True


def test_organizer_missing_directory(tmp_path: Path):
    """Verify organizing a missing directory raises DirectoryNotFoundError."""
    organizer = FileOrganizer()
    with pytest.raises(DirectoryNotFoundError):
        organizer.organize(tmp_path / "does_not_exist")
