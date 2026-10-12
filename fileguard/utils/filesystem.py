"""Filesystem utilities and safety checks for FileGuard.

Centralizes path validation, permission verification, and safe file operations
to avoid duplicating filesystem logic across services and commands.
"""

import os
from pathlib import Path
import shutil
from typing import Union

from fileguard.errors import (
    DirectoryNotFoundError,
    FileOperationError,
    InvalidInputError,
    PermissionDeniedError,
)


def validate_directory(path_input: Union[Path, str]) -> Path:
    """Validate that the given path exists, is a directory, and is accessible.

    Args:
        path_input: Path or path string to validate.

    Returns:
        Resolved Path object representing the validated directory.

    Raises:
        DirectoryNotFoundError: If the path does not exist.
        InvalidInputError: If the path exists but is a file or not a directory.
        PermissionDeniedError: If the directory cannot be accessed.
    """
    try:
        raw_path = Path(path_input)
    except Exception as exc:
        raise InvalidInputError(f"Invalid path syntax: {exc}", path=str(path_input)) from exc

    if not raw_path.exists():
        raise DirectoryNotFoundError(path=str(path_input))

    if raw_path.is_file():
        raise InvalidInputError(path=str(path_input))

    if not raw_path.is_dir():
        raise InvalidInputError(f"Path is not a regular directory.", path=str(path_input))

    check_directory_permissions(raw_path)
    return raw_path


def check_directory_permissions(path: Path) -> None:
    """Verify that a directory can be read and accessed.

    Args:
        path: Path object to inspect.

    Raises:
        PermissionDeniedError: If permissions are insufficient to access the directory.
    """
    try:
        # Check read and execution (search) permission
        if not os.access(path, os.R_OK | os.X_OK):
            raise PermissionDeniedError(path=str(path))
        # Test iterator access
        _ = next(path.iterdir(), None)
    except PermissionError as exc:
        raise PermissionDeniedError(path=str(path)) from exc
    except OSError as exc:
        # On Windows, specific permission errors can appear as OSError with winerror 5 (Access is denied)
        if getattr(exc, "winerror", None) == 5:
            raise PermissionDeniedError(path=str(path)) from exc
        raise


def check_file_readable(path: Path) -> bool:
    """Check if a file can be opened for reading.

    Args:
        path: Path to the file.

    Returns:
        True if readable, False otherwise.
    """
    try:
        if not path.is_file():
            return False
        if not os.access(path, os.R_OK):
            return False
        return True
    except (PermissionError, OSError):
        return False


def is_destination_conflict(destination: Path) -> bool:
    """Check if the target destination already exists.

    Args:
        destination: Path where a file would be moved.

    Returns:
        True if destination already exists, False otherwise.
    """
    return destination.exists()


def safe_move_file(source: Path, destination: Path, force: bool = False) -> None:
    """Safely move a file to destination with conflict handling.

    Args:
        source: Source file path.
        destination: Destination file path.
        force: If True, replace destination if it exists.

    Raises:
        FileOperationError: If move operation fails.
        PermissionDeniedError: If write or delete permission is denied.
    """
    try:
        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            if not force:
                raise FileOperationError(
                    f"Destination already exists: {destination.name}",
                    path=str(destination),
                    hint="Use --force to overwrite existing destination files.",
                )
            # When forcing on Windows, Path.replace handles atomic overwrite if on same drive,
            # or shutil.move if across drives.
            try:
                # Use os.replace for atomic replacement
                os.replace(source, destination)
            except OSError:
                # Fall back to shutil.move
                if destination.is_file():
                    destination.unlink()
                shutil.move(str(source), str(destination))
        else:
            shutil.move(str(source), str(destination))

    except PermissionError as exc:
        raise PermissionDeniedError(
            message="Permission denied during file operation.",
            path=str(destination if destination.exists() else source),
        ) from exc
    except FileOperationError:
        raise
    except Exception as exc:
        raise FileOperationError(
            message=f"Failed to move '{source.name}': {exc}",
            path=str(source),
        ) from exc
