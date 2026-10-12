"""File validator service for FileGuard.

Pre-checks directories and target files for permissions, readability,
destination conflicts, and potential organization issues before performing changes.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from fileguard.config import get_category_for_file
from fileguard.errors import (
    DirectoryNotFoundError,
    InvalidInputError,
    PermissionDeniedError,
)
from fileguard.services.file_scanner import FileScanner
from fileguard.utils.filesystem import check_file_readable, validate_directory


@dataclass
class ValidationResult:
    """Structured result of a directory validation inspection."""

    directory: Path
    is_valid: bool = True
    successful_checks: List[str] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)
    total_files: int = 0
    conflicts: List[Tuple[Path, Path]] = field(default_factory=list)


class FileValidator:
    """Validates directories and potential organization actions without modifying files."""

    def __init__(self, scanner: Optional[FileScanner] = None) -> None:
        self.scanner = scanner or FileScanner()

    def validate(self, directory: Union[Path, str]) -> ValidationResult:
        """Validate a directory prior to organization.

        Args:
            directory: Path to validate.

        Returns:
            ValidationResult with passed checks and detailed problem descriptions.

        Raises:
            DirectoryNotFoundError: If directory does not exist.
            InvalidInputError: If path is a file or invalid.
            PermissionDeniedError: If directory cannot be accessed.
        """
        valid_dir = validate_directory(directory)
        result = ValidationResult(directory=valid_dir)

        # 1. Directory exists and is accessible
        result.successful_checks.append("Directory exists")
        result.successful_checks.append("Directory is accessible")

        # 2. Scan files
        scan_result = self.scanner.scan(valid_dir)
        result.total_files = scan_result.total_files

        # Check for unreadable files
        if scan_result.unreadable_files:
            for unreadable_file, reason in scan_result.unreadable_files:
                result.problems.append(
                    f"File cannot be accessed:\n   {unreadable_file.name}"
                )
        else:
            result.successful_checks.append("Files can be scanned")

        # 3. Check for destination conflicts and name collisions
        destinations_seen: Dict[str, Path] = {}

        for source in scan_result.files:
            category = get_category_for_file(source)
            dest = valid_dir / category / source.name
            dest_rel_str = f"{category}/{source.name}"
            dest_key = dest_rel_str.lower()

            # Does destination already exist on the filesystem?
            if dest.exists() and dest.resolve() != source.resolve():
                result.conflicts.append((source, dest))
                result.problems.append(
                    f"Destination already exists:\n   {dest_rel_str}"
                )

            # Does another file in the same batch collide with this destination?
            elif dest_key in destinations_seen:
                prev_source = destinations_seen[dest_key]
                result.problems.append(
                    f"Case collision between '{source.name}' and '{prev_source.name}' for destination:\n   {dest_rel_str}"
                )
            else:
                destinations_seen[dest_key] = source

        if not result.conflicts and not any("collision" in p for p in result.problems):
            result.successful_checks.append("No destination conflicts found")

        result.is_valid = len(result.problems) == 0
        return result
