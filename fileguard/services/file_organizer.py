"""File organizer service for FileGuard.

Responsible for organizing files into categorized subfolders according to file types.
Supports dry-run preview, force replacement, conflict handling, and detailed statistics.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Union

from fileguard.config import get_category_for_file
from fileguard.errors import (
    DirectoryNotFoundError,
    FileGuardError,
    FileOperationError,
    InvalidInputError,
    PermissionDeniedError,
)
from fileguard.services.file_scanner import FileScanner, ScanResult
from fileguard.utils.filesystem import safe_move_file, validate_directory


@dataclass
class OrganizeOperation:
    """Represents a planned or executed file organization action."""

    source: Path
    destination: Path
    category: str
    status: str  # "moved", "would_move", "skipped", "failed"
    reason: Optional[str] = None


@dataclass
class OrganizeResult:
    """Summary of operations performed by FileOrganizer."""

    directory: Path
    total_files: int = 0
    moved_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    operations: List[OrganizeOperation] = field(default_factory=list)
    is_dry_run: bool = False
    is_empty: bool = False

    @property
    def has_conflicts(self) -> bool:
        """True if any files were skipped due to destination conflicts."""
        return any(op.status == "skipped" for op in self.operations)


class FileOrganizer:
    """Organizes files into category folders."""

    def __init__(self, scanner: Optional[FileScanner] = None) -> None:
        self.scanner = scanner or FileScanner()

    def organize(
        self,
        directory: Union[Path, str],
        dry_run: bool = False,
        force: bool = False,
        on_scan_completed: Optional[Callable[[int], None]] = None,
        on_progress: Optional[Callable[[str, OrganizeOperation], None]] = None,
        on_category_dir_created: Optional[Callable[[str, Path], None]] = None,
    ) -> OrganizeResult:
        """Organize files in the given directory into categorized subdirectories.

        Args:
            directory: Directory to organize.
            dry_run: If True, simulate actions without modifying filesystem.
            force: If True, replace existing destination files.
            on_progress: Callback invoked for each operation (status, op).
            on_category_dir_created: Callback invoked when a category directory is created.

        Returns:
            OrganizeResult with summary statistics and details of each operation.

        Raises:
            DirectoryNotFoundError: If directory does not exist.
            InvalidInputError: If directory is a file or invalid.
            PermissionDeniedError: If permissions are insufficient.
            KeyboardInterrupt: Re-raised if interrupted by user during processing.
        """
        valid_dir = validate_directory(directory)
        scan_result = self.scanner.scan(valid_dir)

        if on_scan_completed:
            on_scan_completed(scan_result.total_files)

        result = OrganizeResult(
            directory=valid_dir,
            total_files=scan_result.total_files,
            is_dry_run=dry_run,
            is_empty=scan_result.total_files == 0,
        )

        if scan_result.total_files == 0:
            return result

        created_categories = set()

        for source in scan_result.files:
            category = get_category_for_file(source)
            category_dir = valid_dir / category
            destination = category_dir / source.name

            # Guard against moving a file to itself
            if source.resolve() == destination.resolve():
                op = OrganizeOperation(
                    source=source,
                    destination=destination,
                    category=category,
                    status="skipped",
                    reason="Source and destination are identical",
                )
                result.operations.append(op)
                result.skipped_files += 1
                if on_progress:
                    on_progress("skipped", op)
                continue

            # Handle DRY-RUN mode
            if dry_run:
                # In dry-run, never perform any filesystem modifications!
                if destination.exists() and not force:
                    op = OrganizeOperation(
                        source=source,
                        destination=destination,
                        category=category,
                        status="skipped",
                        reason="Destination already exists",
                    )
                    result.skipped_files += 1
                else:
                    op = OrganizeOperation(
                        source=source,
                        destination=destination,
                        category=category,
                        status="would_move",
                    )
                    result.moved_files += 1

                result.operations.append(op)
                if on_progress:
                    on_progress(op.status, op)
                continue

            # REAL OPERATION
            # Check destination conflict if force is False
            if destination.exists() and not force:
                op = OrganizeOperation(
                    source=source,
                    destination=destination,
                    category=category,
                    status="skipped",
                    reason="Destination already exists",
                )
                result.operations.append(op)
                result.skipped_files += 1
                if on_progress:
                    on_progress("skipped", op)
                continue

            # Ensure category directory exists
            if category not in created_categories:
                if not category_dir.exists():
                    try:
                        category_dir.mkdir(parents=True, exist_ok=True)
                        if on_category_dir_created:
                            on_category_dir_created(category, category_dir)
                    except PermissionError as exc:
                        raise PermissionDeniedError(
                            message=f"Cannot create category directory '{category}'.",
                            path=str(category_dir),
                        ) from exc
                created_categories.add(category)

            # Move file safely
            try:
                safe_move_file(source, destination, force=force)
                op = OrganizeOperation(
                    source=source,
                    destination=destination,
                    category=category,
                    status="moved",
                )
                result.operations.append(op)
                result.moved_files += 1
                if on_progress:
                    on_progress("moved", op)
            except (FileOperationError, PermissionDeniedError) as exc:
                op = OrganizeOperation(
                    source=source,
                    destination=destination,
                    category=category,
                    status="failed",
                    reason=str(exc),
                )
                result.operations.append(op)
                result.failed_files += 1
                if on_progress:
                    on_progress("failed", op)
            except Exception as exc:
                op = OrganizeOperation(
                    source=source,
                    destination=destination,
                    category=category,
                    status="failed",
                    reason=f"Unexpected error: {exc}",
                )
                result.operations.append(op)
                result.failed_files += 1
                if on_progress:
                    on_progress("failed", op)

        return result
