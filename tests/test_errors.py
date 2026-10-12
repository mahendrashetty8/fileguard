"""Tests for FileGuard custom exceptions and exit codes."""

from fileguard import exit_codes
from fileguard.errors import (
    DirectoryNotFoundError,
    FileGuardError,
    FileOperationError,
    InvalidInputError,
    PermissionDeniedError,
)


def test_exit_codes_constants():
    """Verify that all exit codes match the required specification."""
    assert exit_codes.SUCCESS == 0
    assert exit_codes.GENERAL_ERROR == 1
    assert exit_codes.INVALID_ARGUMENT == 2
    assert exit_codes.FILE_NOT_FOUND == 3
    assert exit_codes.PERMISSION_DENIED == 4
    assert exit_codes.OPERATION_FAILED == 5
    assert exit_codes.INTERRUPTED == 130


def test_base_fileguard_error():
    """Verify FileGuardError base class properties."""
    err = FileGuardError("Something failed", exit_code=1, path="some/path", hint="Try again")
    assert err.message == "Something failed"
    assert err.exit_code == exit_codes.GENERAL_ERROR
    formatted = err.format_error()
    assert "Error: Something failed" in formatted
    assert "Path:" in formatted
    assert "some/path" in formatted
    assert "Try again" in formatted


def test_directory_not_found_error_formatting():
    """Verify DirectoryNotFoundError formatting matches specification."""
    err = DirectoryNotFoundError(path="missing-folder")
    assert err.exit_code == exit_codes.FILE_NOT_FOUND
    formatted = err.format_error()
    assert "Error: Directory not found." in formatted
    assert "Path:\nmissing-folder" in formatted
    assert "Please check that the directory exists." in formatted


def test_invalid_input_error_formatting():
    """Verify InvalidInputError when path is a file matches specification."""
    err = InvalidInputError(path="resume.pdf")
    assert err.exit_code == exit_codes.INVALID_ARGUMENT
    formatted = err.format_error()
    assert "Error: Expected a directory." in formatted
    assert "'resume.pdf' is a file." in formatted
    assert "Please provide a directory path." in formatted


def test_permission_denied_error_formatting():
    """Verify PermissionDeniedError formatting matches specification."""
    err = PermissionDeniedError(path="./protected")
    assert err.exit_code == exit_codes.PERMISSION_DENIED
    formatted = err.format_error()
    assert "Error: Permission denied." in formatted
    assert "FileGuard cannot access:" in formatted
    assert "./protected" in formatted
    assert "Check your permissions and try again." in formatted


def test_file_operation_error():
    """Verify FileOperationError properties and exit code."""
    err = FileOperationError("Failed to move file", path="data.bin")
    assert err.exit_code == exit_codes.OPERATION_FAILED
    formatted = err.format_error()
    assert "Error: Failed to move file" in formatted
