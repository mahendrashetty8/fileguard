"""File scanner service for FileGuard.

Responsible for discovering, inspecting, and categorizing files and directories.
Does not perform CLI output or side-effects.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Union

from fileguard.config import (
    CATEGORY_ORDER,
    DEFAULT_OTHER_CATEGORY,
    get_category_for_file,
)
from fileguard.errors import (
    DirectoryNotFoundError,
    InvalidInputError,
    PermissionDeniedError,
)
from fileguard.utils.filesystem import (
    check_file_readable,
    validate_directory,
)


@dataclass
class ScanResult:
    """Structured result returned by FileScanner."""

    directory: Path
    total_files: int = 0
    total_directories: int = 0
    category_counts: Dict[str, int] = field(default_factory=dict)
    files_by_category: Dict[str, List[Path]] = field(default_factory=dict)
    files: List[Path] = field(default_factory=list)
    directories: List[Path] = field(default_factory=list)
    unreadable_files: List[Tuple[Path, str]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """True if no files exist in the directory."""
        return self.total_files == 0 and self.total_directories == 0

    @property
    def has_files(self) -> bool:
        """True if at least one file was found."""
        return self.total_files > 0


class FileScanner:
    """Scans and categorizes filesystem entries in a directory."""

    def __init__(self) -> None:
        pass

    def scan(self, directory: Union[Path, str]) -> ScanResult:
        """Scan a directory and categorize its contents.

        Args:
            directory: Directory path to scan.

        Returns:
            ScanResult containing discovered file counts and categories.

        Raises:
            DirectoryNotFoundError: If directory does not exist.
            InvalidInputError: If path is a file or invalid.
            PermissionDeniedError: If directory cannot be accessed.
        """
        valid_dir = validate_directory(directory)

        category_counts: Dict[str, int] = {cat: 0 for cat in CATEGORY_ORDER}
        files_by_category: Dict[str, List[Path]] = {cat: [] for cat in CATEGORY_ORDER}
        files: List[Path] = []
        directories: List[Path] = []
        unreadable_files: List[Tuple[Path, str]] = []

        try:
            entries = sorted(list(valid_dir.iterdir()), key=lambda p: p.name.lower())
        except PermissionError as exc:
            raise PermissionDeniedError(path=str(valid_dir)) from exc

        for entry in entries:
            try:
                if entry.is_dir():
                    directories.append(entry)
                elif entry.is_file():
                    files.append(entry)
                    cat = get_category_for_file(entry)
                    if cat not in category_counts:
                        cat = DEFAULT_OTHER_CATEGORY

                    category_counts[cat] = category_counts.get(cat, 0) + 1
                    files_by_category[cat].append(entry)

                    if not check_file_readable(entry):
                        unreadable_files.append((entry, "Permission denied or unreadable"))
            except (PermissionError, OSError) as exc:
                unreadable_files.append((entry, str(exc)))

        return ScanResult(
            directory=valid_dir,
            total_files=len(files),
            total_directories=len(directories),
            category_counts=category_counts,
            files_by_category=files_by_category,
            files=files,
            directories=directories,
            unreadable_files=unreadable_files,
        )
