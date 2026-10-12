"""Organize command for FileGuard CLI.

Moves files into categorized subfolders based on extension, supporting dry-run,
force overwrite, verbose logging, and non-blocking duplicate handling.
"""

import argparse
from pathlib import Path

from fileguard import exit_codes
from fileguard.services.file_organizer import FileOrganizer, OrganizeOperation
from fileguard.utils.formatter import (
    format_dry_run_entry,
    format_dry_run_header,
    format_duplicate_warning,
    format_empty_directory,
    format_interrupt,
    format_organize_summary,
)
from fileguard.utils.logger import get_logger


def execute_organize(args: argparse.Namespace) -> int:
    """Execute the organize command with the given CLI arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code indicating success, warning, or error.
    """
    logger = get_logger()
    logger.verbose = getattr(args, "verbose", False)

    target_path = Path(args.directory)
    dry_run = getattr(args, "dry_run", False)
    force = getattr(args, "force", False)

    logger.info("Scanning directory")

    organizer = FileOrganizer()

    def on_scan_completed(count: int) -> None:
        logger.info(f"Found {count} files")

    def on_category_dir_created(category: str, path: Path) -> None:
        logger.info(f"Creating {category} directory")

    def on_progress(status: str, op: OrganizeOperation) -> None:
        if status == "moved":
            logger.info(f"Moving {op.source.name}")
        elif status == "skipped" and op.reason == "Destination already exists":
            if not dry_run:
                rel_dest = f"{op.category}/{op.source.name}"
                print()
                print(format_duplicate_warning(op.source.name, rel_dest))
                print()
        elif status == "failed":
            logger.error(f"Failed to move {op.source.name}: {op.reason}")

    try:
        result = organizer.organize(
            target_path,
            dry_run=dry_run,
            force=force,
            on_scan_completed=on_scan_completed,
            on_progress=on_progress,
            on_category_dir_created=on_category_dir_created,
        )
    except KeyboardInterrupt:
        print()
        print(format_interrupt())
        return exit_codes.INTERRUPTED

    if result.is_empty:
        print(format_empty_directory(action="organize"))
        return exit_codes.SUCCESS

    if dry_run:
        print(format_dry_run_header())
        print()
        for op in result.operations:
            dest_display = f"{op.category}/{op.source.name}"
            if op.status == "would_move":
                print(format_dry_run_entry(op.source.name, dest_display))
                print()
            elif op.status == "skipped":
                print(f"{op.source.name}\n  [SKIPPED: Destination already exists: {dest_display}]")
                print()
        print("No files were changed.")
        return exit_codes.SUCCESS

    if logger.verbose:
        if result.failed_files == 0:
            print("\nCompleted successfully.")
        else:
            print("\nCompleted with errors.")

    # Print summary of actual changes
    print(
        format_organize_summary(
            total_files=result.total_files,
            moved_files=result.moved_files,
            skipped_files=result.skipped_files,
            failed_files=result.failed_files,
            is_dry_run=False,
        )
    )

    if result.failed_files > 0:
        return exit_codes.OPERATION_FAILED

    return exit_codes.SUCCESS
